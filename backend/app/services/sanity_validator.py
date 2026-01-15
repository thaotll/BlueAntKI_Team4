"""
Sanity Validator for Portfolio Analysis.
Implements a "Truth Table" approach to detect and fix contradictions
in LLM-generated project scores.

This module ensures logical consistency between project status and scores,
preventing contradictory outputs like "Abgeschlossen" + "Kritisch".
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from app.models.scoring import ProjectScore, ScoreValue

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a ProjectScore."""
    score: ProjectScore
    warnings: List[str] = field(default_factory=list)
    corrections_applied: List[str] = field(default_factory=list)
    has_data_error: bool = False


class SanityValidator:
    """
    Validates and corrects contradictions in ProjectScores.
    
    Implements the "Truth Table" logic to ensure:
    - Completed projects don't have high risk/urgency scores
    - Completed projects are never marked as critical
    - Data inconsistencies are flagged appropriately
    - Missing data generates visible warnings
    
    Usage:
        validator = SanityValidator()
        result = validator.validate_and_fix(project_score)
        # result.score contains the corrected score
        # result.warnings contains any data quality warnings
    """
    
    # Keywords indicating a project is completed
    COMPLETED_KEYWORDS = [
        "abgeschlossen", "completed", "fertig", "beendet",
        "closed", "done", "finished", "100%", "erledigt",
        "erfolgreich abgeschlossen", "erfolgreich beendet"
    ]
    
    # Text patterns that should NOT appear in completed project descriptions
    CRITICAL_TEXT_PATTERNS = [
        r"sofortige?\s+eskalation",
        r"kritisch",
        r"critical",
        r"sofort\s+handeln",
        r"unmittelbar(?:e|er)?\s+(?:handlungsbedarf|intervention)",
        r"dringend(?:er)?\s+handlungsbedarf",
        r"management.?intervention",
        r"krisenmanager",
        r"tägliche?\s+status",
    ]
    
    # Tags appended to project names that should be removed (e.g., "[KRITISCH]")
    PROJECT_NAME_TAG_PATTERN = re.compile(
        r"\s*\[(?:KRITISCH|DATEN[- ]?FEHLER|ABGESCHLOSSEN|RISIKO|ZEITKRITISCH)\]\s*",
        re.IGNORECASE,
    )
    
    # Matches quoted segments like 'Projektname' to replace with double quotes
    SINGLE_QUOTE_WRAP_PATTERN = re.compile(
        r"(^|[\s(\[\{\"])'([^'\n]{1,120}?)'(?=[\s)\]\}\.,;!?]|$)"
    )
    
    def __init__(self):
        """Initialize the validator with compiled regex patterns."""
        self._critical_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.CRITICAL_TEXT_PATTERNS
        ]
    
    def validate_and_fix(self, score: ProjectScore) -> ValidationResult:
        """
        Main method: Applies all validation rules to a ProjectScore.

        Args:
            score: The ProjectScore to validate

        Returns:
            ValidationResult containing the corrected score and any warnings
        """
        result = ValidationResult(score=score)

        # Clean up project names before further processing
        self._sanitize_project_name(result)
        self._normalize_text_fields(result)

        # Check if project is completed first
        is_completed = self._is_completed(score)

        if is_completed:
            self._apply_completed_project_rules(result)
        else:
            # Check for stagnant projects that should be marked critical
            self._check_stagnant_project(result)

        # Apply data quality checks (for all projects)
        self._apply_data_quality_checks(result)

        # Validate milestone consistency
        self._validate_milestone_consistency(result, is_completed)

        # Log corrections if any were made
        if result.corrections_applied:
            logger.info(
                f"SanityValidator corrected project '{score.project_name}': "
                f"{', '.join(result.corrections_applied)}"
            )

        if result.warnings:
            logger.warning(
                f"Data warnings for project '{score.project_name}': "
                f"{', '.join(result.warnings)}"
            )

        return result
    
    def validate_portfolio_scores(
        self, 
        scores: List[ProjectScore]
    ) -> Tuple[List[ProjectScore], List[str]]:
        """
        Validate all project scores in a portfolio.
        
        Args:
            scores: List of ProjectScore objects
            
        Returns:
            Tuple of (validated_scores, all_warnings)
        """
        validated_scores = []
        all_warnings = []
        
        for score in scores:
            result = self.validate_and_fix(score)
            validated_scores.append(result.score)
            
            # Add project context to warnings
            for warning in result.warnings:
                all_warnings.append(f"[{score.project_name}] {warning}")
        
        return validated_scores, all_warnings

    def _sanitize_project_name(self, result: ValidationResult) -> None:
        """Remove tag-like markers (e.g., [KRITISCH]) from project names."""
        name = result.score.project_name or ""
        cleaned = self.PROJECT_NAME_TAG_PATTERN.sub(" ", name).strip()
        cleaned = re.sub(r"\s{2,}", " ", cleaned)

        if cleaned != name:
            result.score.project_name = cleaned
            result.corrections_applied.append("Project name sanitized")
    
    def _normalize_text_fields(self, result: ValidationResult) -> None:
        """Ensure summaries and analyses use double quotes instead of single quotes."""
        text_fields = ("summary", "detailed_analysis")
        for field_name in text_fields:
            value = getattr(result.score, field_name, None)
            if not value:
                continue
            normalized = self._normalize_quotes(value)
            if normalized != value:
                setattr(result.score, field_name, normalized)
                result.corrections_applied.append(f"{field_name} quotes normalized")
    
    def _normalize_quotes(self, text: str) -> str:
        """Replace single-quote wrappers with double quotes and normalize curly quotes."""
        if not text:
            return text
        
        def replacer(match: re.Match) -> str:
            prefix = match.group(1)
            content = match.group(2)
            return f"{prefix}\"{content}\""

        normalized = self.SINGLE_QUOTE_WRAP_PATTERN.sub(replacer, text)
        normalized = (
            normalized
            .replace("‚", '"')
            .replace("‘", '"')
            .replace("’", '"')
            .replace("“", '"')
            .replace("”", '"')
        )
        return normalized
    
    def _is_completed(self, score: ProjectScore) -> bool:
        """
        Determine if a project is completed based on status_label or progress.
        
        Args:
            score: The ProjectScore to check
            
        Returns:
            True if the project appears to be completed
        """
        # Check status_label
        if score.status_label:
            status_lower = score.status_label.lower()
            if any(keyword in status_lower for keyword in self.COMPLETED_KEYWORDS):
                return True
        
        # Check if all milestones are completed
        if score.milestones_total > 0 and score.milestones_completed >= score.milestones_total:
            return True
        
        # Check if progress is 100%
        if score.progress_percent >= 100:
            return True
        
        return False
    
    def _apply_completed_project_rules(self, result: ValidationResult) -> None:
        """
        Apply Truth Table rules for completed projects.
        
        Rules:
        1. Risk score should be 0-1 (historical only)
        2. is_critical must be False
        3. Urgency should be 1 (no urgency for completed work)
        4. Remove critical/escalation text from summary/analysis
        """
        score = result.score
        
        # Rule 1: Cap Risk score at 1
        if score.risk.value > 1:
            original_risk = score.risk.value
            score.risk = ScoreValue(
                value=1,
                reasoning=f"Projekt abgeschlossen - Risikobewertung historisch. "
                         f"(Ursprünglicher Wert: {original_risk}/5, retrospektive Analyse)"
            )
            result.corrections_applied.append(f"Risk {original_risk}→1 (completed)")
        
        # Rule 2: Set is_critical to False
        if score.is_critical:
            score.is_critical = False
            result.corrections_applied.append("is_critical→False (completed)")
        
        # Rule 3: Set Urgency to 1
        if score.urgency.value > 1:
            original_urgency = score.urgency.value
            score.urgency = ScoreValue(
                value=1,
                reasoning=f"Projekt abgeschlossen - keine aktive Dringlichkeit. "
                         f"(Ursprünglicher Wert: {original_urgency}/5)"
            )
            result.corrections_applied.append(f"Urgency {original_urgency}→1 (completed)")
        
        # Rule 4: Sanitize text content
        if score.summary:
            sanitized_summary = self._sanitize_completed_text(score.summary)
            if sanitized_summary != score.summary:
                score.summary = sanitized_summary
                result.corrections_applied.append("Summary text sanitized")
        
        if score.detailed_analysis:
            sanitized_analysis = self._sanitize_completed_text(score.detailed_analysis)
            if sanitized_analysis != score.detailed_analysis:
                score.detailed_analysis = sanitized_analysis
                result.corrections_applied.append("Detailed analysis sanitized")
    
    def _sanitize_completed_text(self, text: str) -> str:
        """
        Remove critical/escalation language from text for completed projects.
        
        Replaces urgent phrases with appropriate retrospective language.
        
        Args:
            text: The text to sanitize
            
        Returns:
            Sanitized text without critical language
        """
        if not text:
            return text
        
        sanitized = text
        
        # Replace critical patterns with retrospective language
        replacements = [
            (r"sofortige?\s+eskalation\s+(?:an\s+)?(?:das\s+)?(?:senior\s+)?management",
             "retrospektive Analyse durch das Management"),
            (r"sofort(?:iges?)?\s+handeln\s+erforderlich",
             "wurde erfolgreich abgeschlossen"),
            (r"unmittelbar(?:e|er)?\s+(?:management.?)?intervention",
             "erfolgreiche Projektdurchführung"),
            (r"tägliche?\s+status(?:berichte?)?",
             "abschließende Dokumentation"),
            (r"wöchentliche?\s+steering.?(?:committee.?)?(?:meetings?|reviews?)",
             "Projektabschluss-Review"),
            (r"krisenmanager",
             "Projektleitung"),
            (r"dringend(?:er|es?)?\s+handlungsbedarf",
             "Lessons Learned"),
            (r"\[?KRITISCH\]?",
             "abgeschlossen"),
        ]
        
        for pattern, replacement in replacements:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _apply_data_quality_checks(self, result: ValidationResult) -> None:
        """
        Check for missing or incomplete data and generate warnings.
        
        Args:
            result: The ValidationResult to update with warnings
        """
        score = result.score
        is_completed = self._is_completed(score)
        
        # Warning: No effort booked for active projects
        if score.actual_effort_hours == 0 and not is_completed:
            result.warnings.append(
                "Datenbasis unvollständig: Keine Aufwände gebucht"
            )
        
        # Warning: No planned effort
        if score.planned_effort_hours == 0 and score.actual_effort_hours > 0:
            result.warnings.append(
                "Keine Plan-Aufwände hinterlegt: Abweichungsberechnung nicht möglich"
            )
        
        # Warning: Very low data quality from LLM
        if score.data_quality.value <= 2:
            result.warnings.append(
                "Eingeschränkte Datenqualität: Bewertung mit Vorsicht interpretieren"
            )
    
    def _validate_milestone_consistency(
        self, 
        result: ValidationResult, 
        is_completed: bool
    ) -> None:
        """
        Check for logical inconsistencies in milestone data.
        
        Args:
            result: The ValidationResult to update
            is_completed: Whether the project is completed
        """
        score = result.score
        
        # Critical inconsistency: Completed but no milestones reached
        if is_completed and score.milestones_total > 0:
            if score.milestones_completed == 0:
                result.has_data_error = True
                result.warnings.append(
                    "DATEN-FEHLER: Projekt als abgeschlossen markiert, "
                    "aber 0 von {} Meilensteinen erreicht".format(score.milestones_total)
                )
                # Downgrade data quality
                score.data_quality = ScoreValue(
                    value=1,
                    reasoning="Kritische Daten-Inkonsistenz: Projektstatus 'Abgeschlossen' "
                             "widerspricht Meilenstein-Erfüllung (0/{})".format(
                                 score.milestones_total
                             )
                )
                result.corrections_applied.append("DataQuality→1 (milestone inconsistency)")
        
        # Warning: Milestones delayed in nearly-complete project
        if score.progress_percent >= 90 and score.milestones_delayed > 0:
            result.warnings.append(
                f"Projekt zu {score.progress_percent:.0f}% abgeschlossen, "
                f"aber {score.milestones_delayed} Meilenstein(e) verzögert"
            )

    def _check_stagnant_project(self, result: ValidationResult) -> None:
        """
        Check for stagnant projects that should be marked as critical.

        A stagnant project has:
        - 0% progress AND 0 completed milestones
        - Or very low progress with no milestone completion

        This catches projects the LLM might have missed as critical.

        Args:
            result: The ValidationResult to update
        """
        score = result.score

        # Check if project is in planning phase (should not be marked critical)
        is_planning = False
        if score.status_label:
            planning_keywords = ["planung", "planning", "vorbereitung", "prephase"]
            is_planning = any(kw in score.status_label.lower() for kw in planning_keywords)

        if is_planning:
            return

        # Stagnant project: 0% progress AND 0 milestones completed
        if score.progress_percent == 0 and score.milestones_completed == 0:
            # Only flag if project has milestones defined or planned effort
            if score.milestones_total > 0 or score.planned_effort_hours > 0:
                if not score.is_critical:
                    score.is_critical = True
                    result.corrections_applied.append(
                        "is_critical→True (stagnant: 0% progress, 0 milestones)"
                    )

                # Increase urgency if it's too low
                if score.urgency.value < 4:
                    original_urgency = score.urgency.value
                    score.urgency = ScoreValue(
                        value=4,
                        reasoning=f"Projekt stagniert ohne Fortschritt - erhöhte Dringlichkeit. "
                                  f"(Ursprünglich: {original_urgency}/5)"
                    )
                    result.corrections_applied.append(
                        f"Urgency {original_urgency}→4 (stagnant project)"
                    )

                # Increase risk if it's too low
                if score.risk.value < 4:
                    original_risk = score.risk.value
                    score.risk = ScoreValue(
                        value=4,
                        reasoning=f"Erhöhtes Risiko durch fehlenden Projektfortschritt. "
                                  f"(Ursprünglich: {original_risk}/5)"
                    )
                    result.corrections_applied.append(
                        f"Risk {original_risk}→4 (stagnant project)"
                    )

                result.warnings.append(
                    "Projekt ohne Fortschritt: 0% abgeschlossen, keine Meilensteine erreicht"
                )

        # Project with milestones but none completed (less severe)
        elif score.milestones_total > 0 and score.milestones_completed == 0:
            if score.progress_percent < 20:
                result.warnings.append(
                    f"Keine Meilensteine erreicht bei {score.progress_percent:.0f}% Fortschritt"
                )
                # Mark as critical if not already
                if not score.is_critical and score.progress_percent < 10:
                    score.is_critical = True
                    result.corrections_applied.append(
                        "is_critical→True (no milestones, <10% progress)"
                    )

    def has_data_mismatch(self, score: ProjectScore) -> bool:
        """
        Check if a project has contradictory data that invalidates its status.
        
        A data mismatch occurs when a project is marked as "completed" BUT:
        - 0 milestones completed (when milestones exist)
        - 0% progress
        - No effort booked at all
        
        This indicates the BlueAnt status is likely incorrect (project may be
        STOPPED or CRITICAL, not successfully completed).
        """
        is_completed = self._is_completed(score)
        
        if not is_completed:
            return False
        
        # Check for contradictions
        # Mismatch: Completed but 0 milestones reached
        if score.milestones_total > 0 and score.milestones_completed == 0:
            return True
        
        # Mismatch: Completed but 0% progress
        if score.progress_percent == 0:
            return True
        
        # Mismatch: Completed but no effort booked (when effort was planned)
        if score.actual_effort_hours == 0 and score.planned_effort_hours > 0:
            return True
        
        return False

    def get_project_label(self, score: ProjectScore) -> str:
        """
        Determine the appropriate display label for a project.
        
        Args:
            score: The ProjectScore to label
            
        Returns:
            Appropriate label string
        """
        is_completed = self._is_completed(score)
        
        if is_completed:
            # Check for data errors using comprehensive mismatch detection
            if self.has_data_mismatch(score):
                return "Daten-Fehler"
            return "Review / Lessons Learned"
        
        if score.is_critical:
            return "Kritisch"
        
        if score.risk.value >= 4:
            return "Risikobehaftet"
        
        if score.urgency.value >= 4:
            return "Zeitkritisch"
        
        return "Standard"


def get_sanity_validator() -> SanityValidator:
    """Get a SanityValidator instance."""
    return SanityValidator()

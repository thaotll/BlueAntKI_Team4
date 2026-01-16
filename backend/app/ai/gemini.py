"""
Gemini LLM client for project scoring and portfolio analysis.
"""

import json
import logging
import re
from typing import List, Optional

import google.generativeai as genai

from app.config import get_settings
from app.models.domain import NormalizedPortfolio, NormalizedProject
from app.models.scoring import PortfolioAnalysis, ProjectScore, ScoreValue
from app.ai.prompts import (
    PORTFOLIO_ANALYSIS_PROMPT_TEMPLATE,
    SCORING_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
    PRESENTATION_STRUCTURE_SYSTEM_PROMPT,
    PRESENTATION_STRUCTURE_PROMPT_TEMPLATE,
    format_project_for_prompt,
    format_scores_for_portfolio_prompt,
    format_analysis_for_presentation_prompt,
)
from app.models.pptx import (
    AIPresentationStructure,
    AISlideSpec,
    SlideVisualization,
    SlideType,
    VisualizationType,
)
from app.services.sanity_validator import SanityValidator

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Exception raised for Gemini API errors."""
    pass


class GeminiService:
    """
    Client for Gemini-based project scoring.

    Implements the 2-phase analysis:
    1. Phase 1: Score individual projects (U/I/C/R/DQ)
    2. Phase 2: Generate portfolio-level analysis
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model

        if not self.api_key:
            logger.warning("Gemini API key not configured!")
            return

        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_PROMPT,
        )
        # Slight randomness during scoring encourages differentiated outputs
        self.scoring_generation_config = genai.GenerationConfig(
            temperature=0.3,
            top_p=0.9,
            top_k=40,
        )

        logger.info(f"Gemini service initialized with model: {self.model_name}")

    def _repair_json(self, text: str) -> str:
        """Attempt to repair common JSON issues from LLM responses."""
        # Remove trailing commas before } or ]
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix missing commas between objects in arrays: }{ -> },{
        text = re.sub(r'\}(\s*)\{', r'},\1{', text)
        
        # Fix missing commas after string values: "value" "key" -> "value", "key"
        text = re.sub(r'"\s*\n\s*"', '",\n"', text)
        
        # Remove control characters that break JSON
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        
        return text

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response text with robust error handling."""
        if not text or not text.strip():
            logger.error("Empty text provided to _extract_json")
            raise GeminiError("LLM returned empty response")
        
        original_text = text
        
        # Try to find JSON in code blocks first
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        if matches:
            text = matches[0]
            logger.debug("Found JSON in code block")

        text = text.strip()
        
        # Handle potential markdown or extra text
        # Find the first { and last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]
        else:
            # Try to find array format
            start_idx = text.find('[')
            end_idx = text.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                text = text[start_idx:end_idx + 1]
                # Wrap in object if it's an array
                text = '{"projects": ' + text + '}'
                logger.debug("Found array format, wrapped in object")

        # First attempt: try parsing as-is
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}, attempting repair...")
        
        # Second attempt: repair common JSON issues
        repaired_text = self._repair_json(text)
        try:
            result = json.loads(repaired_text)
            logger.info("JSON repair successful")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Repaired JSON still invalid: {e}")
        
        # Third attempt: try to extract just the projects array if present
        projects_pattern = r'"projects"\s*:\s*\[([\s\S]*?)\]'
        projects_match = re.search(projects_pattern, text)
        if projects_match:
            try:
                projects_text = '[' + projects_match.group(1) + ']'
                projects_text = self._repair_json(projects_text)
                projects = json.loads(projects_text)
                logger.info("Extracted projects array successfully")
                return {"projects": projects}
            except json.JSONDecodeError:
                pass
        
        # Log detailed error info
        logger.error(f"Failed to parse JSON after all attempts")
        logger.error(f"Extracted text (first 1500 chars): {text[:1500]}")
        logger.error(f"Original text (first 500 chars): {original_text[:500]}")
        raise GeminiError(f"Failed to parse LLM response as JSON: Invalid JSON structure")

    def _parse_project_score(self, data: dict) -> ProjectScore:
        """Parse a single project score from LLM response."""
        return ProjectScore(
            project_id=data.get("project_id", "unknown"),
            project_name=data.get("project_name", "Unknown"),
            urgency=ScoreValue(
                value=data.get("urgency", {}).get("value", 3),
                reasoning=data.get("urgency", {}).get("reasoning", "Keine Begründung"),
            ),
            importance=ScoreValue(
                value=data.get("importance", {}).get("value", 3),
                reasoning=data.get("importance", {}).get("reasoning", "Keine Begründung"),
            ),
            complexity=ScoreValue(
                value=data.get("complexity", {}).get("value", 3),
                reasoning=data.get("complexity", {}).get("reasoning", "Keine Begründung"),
            ),
            risk=ScoreValue(
                value=data.get("risk", {}).get("value", 3),
                reasoning=data.get("risk", {}).get("reasoning", "Keine Begründung"),
            ),
            data_quality=ScoreValue(
                value=data.get("data_quality", {}).get("value", 3),
                reasoning=data.get("data_quality", {}).get("reasoning", "Keine Begründung"),
            ),
            is_critical=data.get("is_critical", False),
            summary=data.get("summary", ""),
            detailed_analysis=data.get("detailed_analysis", ""),
        )

    async def score_projects(
        self,
        projects: List[NormalizedProject],
        batch_size: int = 6,
        max_json_retries: int = 2,
    ) -> List[ProjectScore]:
        """
        Phase 1: Score multiple projects using Gemini.
        
        Includes retry logic for JSON parsing failures.
        """
        if not self.api_key:
            raise GeminiError("Gemini API key not configured")

        all_scores: List[ProjectScore] = []

        for i in range(0, len(projects), batch_size):
            batch = projects[i : i + batch_size]
            logger.info(
                f"Scoring projects batch {i // batch_size + 1} ({len(batch)} projects)"
            )

            project_data_text = "\n".join(
                format_project_for_prompt(p.model_dump()) for p in batch
            )

            prompt = SCORING_PROMPT_TEMPLATE.format(project_data=project_data_text)
            
            batch_scores = None
            last_error = None
            
            # Retry loop for JSON parsing issues
            for json_attempt in range(max_json_retries + 1):
                try:
                    if json_attempt > 0:
                        logger.info(f"Retry attempt {json_attempt}/{max_json_retries} for JSON parsing...")
                    
                    # Use different generation config on retry
                    generation_config = self.scoring_generation_config
                    if json_attempt > 0:
                        generation_config = genai.GenerationConfig(
                            temperature=min(0.7 + (json_attempt * 0.15), 1.2),
                            top_p=0.95,
                            top_k=50,
                        )
                    
                    response = self.model.generate_content(
                        prompt,
                        generation_config=generation_config,
                    )
                    response_data = self._extract_json(response.text)
                    
                    batch_scores = []
                    for score_data in response_data.get("projects", []):
                        try:
                            score = self._parse_project_score(score_data)
                            batch_scores.append(score)
                        except Exception as e:
                            logger.warning(f"Failed to parse score for project: {e}")
                            batch_scores.append(
                                ProjectScore(
                                    project_id=score_data.get("project_id", "unknown"),
                                    project_name=score_data.get("project_name", "Unknown"),
                                    urgency=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    importance=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    complexity=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    risk=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    data_quality=ScoreValue(value=1, reasoning="Fehler bei der Analyse"),
                                    is_critical=False,
                                    summary="Fehler bei der Analyse dieses Projekts",
                                    detailed_analysis="Die Analyse dieses Projekts konnte aufgrund eines technischen Fehlers nicht vollständig durchgeführt werden. Bitte überprüfen Sie die Eingabedaten.",
                                )
                            )
                    
                    # Success - break out of retry loop
                    break
                    
                except GeminiError as e:
                    last_error = e
                    if "Failed to parse LLM response as JSON" in str(e):
                        if json_attempt < max_json_retries:
                            logger.warning(f"JSON parsing failed, retrying ({json_attempt + 1}/{max_json_retries})...")
                            continue
                    # Re-raise other errors or final attempt
                    if json_attempt >= max_json_retries:
                        logger.error(f"All JSON parsing attempts failed: {e}")
                        raise GeminiError(f"Failed to score projects: {e}")
                    raise
                    
                except Exception as e:
                    logger.error(f"Gemini API error during scoring: {e}")
                    raise GeminiError(f"Failed to score projects: {e}")
            
            if batch_scores is None:
                raise last_error or GeminiError("Failed to score projects: Unknown error")
                
            all_scores.extend(batch_scores)

        return all_scores

    async def analyze_portfolio(
        self,
        portfolio: NormalizedPortfolio,
        project_scores: List[ProjectScore],
    ) -> PortfolioAnalysis:
        """
        Phase 2: Generate portfolio-level analysis based on project scores.
        """
        if not self.api_key:
            raise GeminiError("Gemini API key not configured")

        logger.info(f"Generating portfolio analysis for: {portfolio.name}")

        scores_summary = format_scores_for_portfolio_prompt(
            [s.model_dump() for s in project_scores]
        )

        prompt = PORTFOLIO_ANALYSIS_PROMPT_TEMPLATE.format(
            portfolio_name=portfolio.name,
            scores_summary=scores_summary,
        )

        try:
            response = self.model.generate_content(prompt)
            response_data = self._extract_json(response.text)

            analysis = PortfolioAnalysis(
                portfolio_id=portfolio.id,
                portfolio_name=portfolio.name,
                project_scores=project_scores,
                executive_summary=response_data.get("executive_summary", ""),
                critical_projects=response_data.get("critical_projects", []),
                priority_ranking=response_data.get("priority_ranking", []),
                risk_clusters=response_data.get("risk_clusters", []),
                recommendations=response_data.get("recommendations", []),
            )

            analysis.compute_statistics()
            return analysis

        except Exception as e:
            logger.error(f"Gemini API error during portfolio analysis: {e}")
            raise GeminiError(f"Failed to analyze portfolio: {e}")

    def _enrich_scores_with_normalized_data(
        self,
        project_scores: List[ProjectScore],
        portfolio: NormalizedPortfolio,
    ) -> None:
        """Enrich ProjectScore objects with data from NormalizedProject."""
        normalized_by_id = {p.id: p for p in portfolio.projects}

        for score in project_scores:
            normalized = normalized_by_id.get(score.project_id)
            if normalized:
                score.progress_percent = normalized.progress_percent
                score.owner_name = normalized.owner_name
                score.status_color = normalized.status_color.value if normalized.status_color else "gray"
                score.status_label = normalized.status_label
                score.milestones_total = normalized.milestones_total
                score.milestones_completed = normalized.milestones_completed
                score.milestones_delayed = normalized.milestones_delayed
                score.planned_effort_hours = normalized.planned_effort_hours
                score.actual_effort_hours = normalized.actual_effort_hours
                score.has_status_mismatch = normalized.has_status_mismatch
                score.status_mismatch_reasons = normalized.status_mismatch_reasons

    async def full_analysis(
        self,
        portfolio: NormalizedPortfolio,
    ) -> PortfolioAnalysis:
        """Run complete 2-phase analysis on a portfolio."""
        logger.info(
            f"Starting full analysis for portfolio: {portfolio.name} "
            f"({len(portfolio.projects)} projects)"
        )

        # Phase 1: Score individual projects
        project_scores = await self.score_projects(portfolio.projects)

        # Enrich scores with normalized data for reporting (BEFORE validation)
        # This ensures the validator has access to status_label, milestones, etc.
        self._enrich_scores_with_normalized_data(project_scores, portfolio)

        # Phase 1.5: Sanity Validation - Fix contradictions
        # This step ensures logical consistency (e.g., completed projects aren't "critical")
        validator = SanityValidator()
        validated_scores, data_warnings = validator.validate_portfolio_scores(project_scores)
        
        logger.info(
            f"Sanity validation complete. {len(data_warnings)} warnings generated."
        )

        # Phase 2: Portfolio-level analysis with validated scores
        analysis = await self.analyze_portfolio(portfolio, validated_scores)
        
        # Attach data quality warnings to the analysis
        analysis.data_warnings = data_warnings

        logger.info(
            f"Analysis complete. Critical projects: {len(analysis.critical_projects)}, "
            f"Data warnings: {len(data_warnings)}"
        )

        return analysis

    async def generate_presentation_structure(
        self,
        analysis: PortfolioAnalysis,
    ) -> AIPresentationStructure:
        """
        Generate AI-optimized presentation structure based on portfolio analysis.
        
        Args:
            analysis: Complete portfolio analysis with scores
            
        Returns:
            AIPresentationStructure with recommended slides and visualizations
        """
        if not self.api_key:
            raise GeminiError("Gemini API key not configured")

        logger.info(f"Generating presentation structure for: {analysis.portfolio_name}")

        # Format analysis data for the prompt
        prompt_data = format_analysis_for_presentation_prompt(analysis)
        
        prompt = PRESENTATION_STRUCTURE_PROMPT_TEMPLATE.format(**prompt_data)

        try:
            # Use a presentation-specific model instance with appropriate system prompt
            presentation_model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=PRESENTATION_STRUCTURE_SYSTEM_PROMPT,
            )
            
            response = presentation_model.generate_content(prompt)
            response_data = self._extract_json(response.text)

            # Parse slides
            slides = []
            for slide_data in response_data.get("slides", []):
                # Parse visualizations
                visualizations = []
                for viz_data in slide_data.get("visualizations", []):
                    try:
                        viz = SlideVisualization(
                            visualization_type=VisualizationType(viz_data.get("visualization_type", "bar_chart")),
                            data_source=viz_data.get("data_source", ""),
                            description=viz_data.get("description", ""),
                            position_hint=viz_data.get("position_hint", "full"),
                        )
                        visualizations.append(viz)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to parse visualization: {e}")
                
                try:
                    slide_spec = AISlideSpec(
                        slide_type=SlideType(slide_data.get("slide_type", "statistics")),
                        title=slide_data.get("title", ""),
                        subtitle=slide_data.get("subtitle"),
                        visualizations=visualizations,
                        key_message=slide_data.get("key_message"),
                        speaker_notes=slide_data.get("speaker_notes"),
                    )
                    slides.append(slide_spec)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse slide: {e}")

            structure = AIPresentationStructure(
                slides=slides,
                total_estimated_slides=response_data.get("total_estimated_slides", len(slides)),
            )

            logger.info(f"Generated presentation structure with {len(slides)} slides")
            return structure

        except Exception as e:
            logger.error(f"Failed to generate presentation structure: {e}", exc_info=True)
            # Return a default structure if AI generation fails
            return self._get_default_presentation_structure(analysis)

    def _get_default_presentation_structure(
        self,
        analysis: PortfolioAnalysis,
    ) -> AIPresentationStructure:
        """Return a default presentation structure if AI generation fails."""
        logger.info("Using default presentation structure")
        
        slides = [
            AISlideSpec(
                slide_type=SlideType.TITLE,
                title=analysis.portfolio_name,
                subtitle="KI-gestützte Portfolioanalyse",
            ),
            AISlideSpec(
                slide_type=SlideType.EXECUTIVE_SUMMARY,
                title="Executive Summary",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.METRIC_CARDS,
                        data_source="key_metrics",
                        description="Wichtigste Kennzahlen des Portfolios",
                        position_hint="full",
                    ),
                ],
                key_message=analysis.executive_summary[:200] if analysis.executive_summary else None,
            ),
            AISlideSpec(
                slide_type=SlideType.STATISTICS,
                title="Portfolio-Scores im Überblick",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.BAR_CHART,
                        data_source="avg_scores",
                        description="Durchschnittliche U/I/C/R/DQ Werte",
                        position_hint="left",
                    ),
                    SlideVisualization(
                        visualization_type=VisualizationType.PIE_CHART,
                        data_source="status_distribution",
                        description="Verteilung der Projektstatus",
                        position_hint="right",
                    ),
                ],
            ),
            AISlideSpec(
                slide_type=SlideType.RISK_MATRIX,
                title="Risiko-Dringlichkeits-Matrix",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.SCATTER_PLOT,
                        data_source="risk_urgency",
                        description="Projekte nach Risiko und Dringlichkeit",
                        position_hint="full",
                    ),
                ],
            ),
            AISlideSpec(
                slide_type=SlideType.CRITICAL_PROJECTS,
                title="Kritische Projekte",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.TABLE,
                        data_source="critical_projects",
                        description="Übersicht kritischer Projekte",
                        position_hint="full",
                    ),
                ],
            ),
            AISlideSpec(
                slide_type=SlideType.RECOMMENDATIONS,
                title="Handlungsempfehlungen",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.BULLET_POINTS,
                        data_source="recommendations",
                        description="Priorisierte Empfehlungen",
                        position_hint="full",
                    ),
                ],
            ),
        ]
        
        return AIPresentationStructure(
            slides=slides,
            total_estimated_slides=len(slides),
        )


def get_gemini_service() -> GeminiService:
    """Get a Gemini service instance."""
    return GeminiService()

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
    format_project_for_prompt,
    format_scores_for_portfolio_prompt,
)

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

        logger.info(f"Gemini service initialized with model: {self.model_name}")

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response text."""
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        if matches:
            text = matches[0]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw text: {text[:500]}...")
            raise GeminiError(f"Failed to parse LLM response as JSON: {e}")

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
        )

    async def score_projects(
        self,
        projects: List[NormalizedProject],
        batch_size: int = 10,
    ) -> List[ProjectScore]:
        """
        Phase 1: Score multiple projects using Gemini.
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

            try:
                response = self.model.generate_content(prompt)
                response_data = self._extract_json(response.text)

                for score_data in response_data.get("projects", []):
                    try:
                        score = self._parse_project_score(score_data)
                        all_scores.append(score)
                    except Exception as e:
                        logger.warning(f"Failed to parse score for project: {e}")
                        all_scores.append(
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
                            )
                        )

            except Exception as e:
                logger.error(f"Gemini API error during scoring: {e}")
                raise GeminiError(f"Failed to score projects: {e}")

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
                score.milestones_total = normalized.milestones_total
                score.milestones_completed = normalized.milestones_completed
                score.milestones_delayed = normalized.milestones_delayed
                score.planned_effort_hours = normalized.planned_effort_hours
                score.actual_effort_hours = normalized.actual_effort_hours

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

        # Enrich scores with normalized data for reporting
        self._enrich_scores_with_normalized_data(project_scores, portfolio)

        # Phase 2: Portfolio-level analysis
        analysis = await self.analyze_portfolio(portfolio, project_scores)

        logger.info(
            f"Analysis complete. Critical projects: {len(analysis.critical_projects)}"
        )

        return analysis


def get_gemini_service() -> GeminiService:
    """Get a Gemini service instance."""
    return GeminiService()

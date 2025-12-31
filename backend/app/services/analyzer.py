"""
Portfolio Analyzer Service.
Orchestrates the full analysis pipeline from BlueAnt data to AI scoring.
"""

import logging
from typing import Optional

from app.ai.gemini import GeminiService
from app.models.domain import NormalizedPortfolio
from app.models.scoring import PortfolioAnalysis
from app.services.blueant import BlueAntService
from app.services.normalizer import DataNormalizer

logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """
    Orchestrates the complete portfolio analysis pipeline.

    Steps:
    1. Fetch portfolio and projects from BlueAnt
    2. Normalize data for LLM consumption
    3. Run AI scoring (Phase 1: projects, Phase 2: portfolio)
    4. Return complete analysis
    """

    def __init__(
        self,
        blueant: BlueAntService,
        gemini: GeminiService,
    ):
        self.blueant = blueant
        self.gemini = gemini
        self.normalizer = DataNormalizer()

    async def analyze_portfolio(
        self,
        portfolio_id: str,
    ) -> PortfolioAnalysis:
        """
        Run full analysis pipeline on a portfolio.

        Args:
            portfolio_id: BlueAnt portfolio ID

        Returns:
            Complete PortfolioAnalysis with scores and insights
        """
        logger.info(f"Starting analysis for portfolio: {portfolio_id}")

        # Step 1: Fetch data from BlueAnt
        portfolio = await self.blueant.get_portfolio(portfolio_id)
        raw_projects = await self.blueant.get_portfolio_projects(portfolio_id)
        status_masterdata = await self.blueant.get_status_masterdata()

        logger.info(f"Fetched {len(raw_projects)} projects from BlueAnt")

        # Step 2: Normalize data
        self.normalizer.set_status_masterdata(status_masterdata)

        normalized_projects = []
        for project in raw_projects:
            try:
                planning_entries = await self.blueant.get_project_planning_entries(project.id)
                normalized = self.normalizer.normalize_project(project, planning_entries)
                normalized_projects.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize project {project.id}: {e}")

        normalized_portfolio = self.normalizer.normalize_portfolio(
            portfolio, normalized_projects
        )

        logger.info(f"Normalized {len(normalized_projects)} projects")

        # Step 3: Run AI analysis
        analysis = await self.gemini.full_analysis(normalized_portfolio)

        logger.info(
            f"Analysis complete. Found {len(analysis.critical_projects)} critical projects"
        )

        return analysis

    async def get_normalized_portfolio(
        self,
        portfolio_id: str,
    ) -> NormalizedPortfolio:
        """
        Get normalized portfolio data without AI analysis.
        Useful for previewing data before running full analysis.
        """
        portfolio = await self.blueant.get_portfolio(portfolio_id)
        raw_projects = await self.blueant.get_portfolio_projects(portfolio_id)
        status_masterdata = await self.blueant.get_status_masterdata()

        self.normalizer.set_status_masterdata(status_masterdata)

        normalized_projects = []
        for project in raw_projects:
            try:
                planning_entries = await self.blueant.get_project_planning_entries(project.id)
                normalized = self.normalizer.normalize_project(project, planning_entries)
                normalized_projects.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize project {project.id}: {e}")

        return self.normalizer.normalize_portfolio(portfolio, normalized_projects)

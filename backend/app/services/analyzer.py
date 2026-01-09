"""
Portfolio Analyzer Service.
Orchestrates the full analysis pipeline from BlueAnt data to AI scoring.

Supports multiple LLM providers:
- Gemini (Google)
- OpenRouter (Mistral, Google)
"""

import logging
from typing import Optional, Union

from app.ai.gemini import GeminiService
from app.ai.openrouter import OpenRouterService
from app.ai.llm_factory import get_llm_service, LLMProvider
from app.models.domain import NormalizedPortfolio
from app.models.scoring import PortfolioAnalysis
from app.services.blueant import BlueAntService
from app.services.normalizer import DataNormalizer

logger = logging.getLogger(__name__)

# Type alias for LLM services
LLMService = Union[GeminiService, OpenRouterService]


class PortfolioAnalyzer:
    """
    Orchestrates the complete portfolio analysis pipeline.

    Steps:
    1. Fetch portfolio and projects from BlueAnt
    2. Normalize data for LLM consumption
    3. Run AI scoring (Phase 1: projects, Phase 2: portfolio)
    4. Return complete analysis
    
    Supports multiple LLM providers via the llm_service parameter.
    """

    def __init__(
        self,
        blueant: BlueAntService,
        llm_service: Optional[LLMService] = None,
        # Legacy parameter for backwards compatibility
        gemini: Optional[GeminiService] = None,
    ):
        self.blueant = blueant
        
        # Support both new llm_service and legacy gemini parameter
        if llm_service is not None:
            self.llm_service = llm_service
        elif gemini is not None:
            self.llm_service = gemini
        else:
            # Use factory to get configured default
            self.llm_service = get_llm_service()
            
        self.normalizer = DataNormalizer()
        
        # Log which provider is being used
        provider_name = type(self.llm_service).__name__
        logger.info(f"PortfolioAnalyzer initialized with LLM service: {provider_name}")

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

        # Step 1: Fetch data from BlueAnt (parallel fetch for performance)
        import asyncio
        
        portfolio_task = self.blueant.get_portfolio(portfolio_id)
        projects_task = self.blueant.get_portfolio_projects(portfolio_id)
        masterdata_task = self.blueant.get_all_masterdata()
        
        portfolio, raw_projects, masterdata = await asyncio.gather(
            portfolio_task, projects_task, masterdata_task
        )

        logger.info(f"Fetched {len(raw_projects)} projects from BlueAnt")
        logger.info(f"Loaded masterdata: {len(masterdata.get('statuses', []))} statuses, "
                   f"{len(masterdata.get('priorities', []))} priorities, "
                   f"{len(masterdata.get('types', []))} types, "
                   f"{len(masterdata.get('departments', []))} departments, "
                   f"{len(masterdata.get('customers', []))} customers")

        # Step 2: Normalize data with all masterdata
        self.normalizer.set_all_masterdata(masterdata)

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
        analysis = await self.llm_service.full_analysis(normalized_portfolio)

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
        import asyncio
        
        portfolio_task = self.blueant.get_portfolio(portfolio_id)
        projects_task = self.blueant.get_portfolio_projects(portfolio_id)
        masterdata_task = self.blueant.get_all_masterdata()
        
        portfolio, raw_projects, masterdata = await asyncio.gather(
            portfolio_task, projects_task, masterdata_task
        )

        self.normalizer.set_all_masterdata(masterdata)

        normalized_projects = []
        for project in raw_projects:
            try:
                planning_entries = await self.blueant.get_project_planning_entries(project.id)
                normalized = self.normalizer.normalize_project(project, planning_entries)
                normalized_projects.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize project {project.id}: {e}")

        return self.normalizer.normalize_portfolio(portfolio, normalized_projects)

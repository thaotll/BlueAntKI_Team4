"""
Analysis API endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import APIRouter

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, CustomConfig
from app.ai.gemini import GeminiError, GeminiService, get_gemini_service
from app.services.analyzer import PortfolioAnalyzer
from app.services.blueant import BlueAntClientError, BlueAntService, get_blueant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])


def _get_services(custom_config: Optional[CustomConfig]) -> Tuple[BlueAntService, GeminiService]:
    """Get services with optional custom config."""
    if custom_config and (custom_config.blueant_url or custom_config.blueant_key):
        blueant = BlueAntService(
            base_url=custom_config.blueant_url,
            api_key=custom_config.blueant_key,
        )
    else:
        blueant = get_blueant_service()

    if custom_config and custom_config.gemini_key:
        gemini = GeminiService(api_key=custom_config.gemini_key)
    else:
        gemini = get_gemini_service()

    return blueant, gemini


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_portfolio(request: AnalyzeRequest):
    """
    Analyze a portfolio from BlueAnt.

    This endpoint:
    1. Fetches all projects for the given portfolio from BlueAnt
    2. Normalizes the data into a consistent structure
    3. Sends data to Gemini for U/I/C/R/DQ scoring (Phase 1)
    4. Generates portfolio-level analysis (Phase 2)
    5. Returns the complete analysis result
    """
    start_time = datetime.now(timezone.utc)
    portfolio_id = request.portfolio_id

    logger.info(f"Starting portfolio analysis for: {portfolio_id}")

    try:
        # Initialize services
        blueant, gemini = _get_services(request.custom_config)
        analyzer = PortfolioAnalyzer(blueant, gemini)

        # Run analysis
        analysis = await analyzer.analyze_portfolio(portfolio_id)

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        logger.info(f"Analysis completed in {duration:.1f}s")

        return AnalyzeResponse(
            success=True,
            analysis=analysis,
            metadata={
                "portfolio_id": portfolio_id,
                "duration_seconds": duration,
                "project_count": len(analysis.project_scores),
                "critical_count": len(analysis.critical_projects),
            },
        )

    except BlueAntClientError as e:
        logger.error(f"BlueAnt error: {e}")
        return AnalyzeResponse(
            success=False,
            error=f"BlueAnt Fehler: {e}",
        )

    except GeminiError as e:
        logger.error(f"Gemini error: {e}")
        return AnalyzeResponse(
            success=False,
            error=f"KI-Analyse Fehler: {e}",
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return AnalyzeResponse(
            success=False,
            error=f"Unerwarteter Fehler: {e}",
        )

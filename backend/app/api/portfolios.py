"""
Portfolio API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    CustomConfig,
    PortfolioSearchRequest,
    PortfolioSearchResponse,
    PortfolioSummary,
)
from app.services.blueant import BlueAntClientError, BlueAntService, get_blueant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolios", tags=["Portfolios"])


def _get_blueant(custom_config: Optional[CustomConfig]) -> BlueAntService:
    """Get BlueAnt service with optional custom config."""
    if custom_config and (custom_config.blueant_url or custom_config.blueant_key):
        return BlueAntService(
            base_url=custom_config.blueant_url,
            api_key=custom_config.blueant_key,
        )
    return get_blueant_service()


@router.post("/search", response_model=PortfolioSearchResponse)
async def search_portfolios(request: PortfolioSearchRequest):
    """
    Search portfolios by name.

    Returns matching portfolios with basic info.
    """
    logger.info(f"Searching portfolios for: {request.name}")

    try:
        blueant = _get_blueant(request.custom_config)
        portfolios = await blueant.search_portfolios(request.name)

        results = [
            PortfolioSummary(
                id=str(p.id),
                name=p.name,
                project_count=len(p.project_ids),
                description=p.description,
            )
            for p in portfolios
        ]

        logger.info(f"Found {len(results)} matching portfolios")

        return PortfolioSearchResponse(
            success=True,
            portfolios=results,
        )

    except BlueAntClientError as e:
        logger.error(f"BlueAnt error during search: {e}")
        return PortfolioSearchResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        return PortfolioSearchResponse(
            success=False,
            error=f"Unexpected error: {e}",
        )


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """
    Get portfolio details by ID.
    """
    try:
        blueant = get_blueant_service()
        portfolio = await blueant.get_portfolio(portfolio_id)

        return {
            "success": True,
            "portfolio": {
                "id": str(portfolio.id),
                "name": portfolio.name,
                "description": portfolio.description,
                "project_count": len(portfolio.project_ids),
                "project_ids": portfolio.project_ids,
            },
        }

    except BlueAntClientError as e:
        raise HTTPException(status_code=404, detail=f"Portfolio not found: {e}")

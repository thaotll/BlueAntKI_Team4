"""
API request/response schemas.
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.scoring import PortfolioAnalysis


class CustomConfig(BaseModel):
    """Custom API configuration that overrides .env settings."""

    blueant_url: Optional[str] = Field(None, description="BlueAnt API base URL")
    blueant_key: Optional[str] = Field(None, description="BlueAnt API key")
    gemini_key: Optional[str] = Field(None, description="Gemini API key")


# =============================================================================
# Portfolio Endpoints
# =============================================================================


class PortfolioSearchRequest(BaseModel):
    """Request body for portfolio search."""

    name: str = Field(..., description="Portfolio name to search for")
    custom_config: Optional[CustomConfig] = None


class PortfolioSummary(BaseModel):
    """Brief portfolio info for search results."""

    id: str
    name: str
    project_count: int = 0
    description: Optional[str] = None


class PortfolioSearchResponse(BaseModel):
    """Response from portfolio search."""

    success: bool
    portfolios: list[PortfolioSummary] = Field(default_factory=list)
    error: Optional[str] = None


# =============================================================================
# Analysis Endpoints
# =============================================================================


class AnalyzeRequest(BaseModel):
    """Request body for portfolio analysis."""

    portfolio_id: str = Field(..., description="BlueAnt Portfolio ID to analyze")
    custom_config: Optional[CustomConfig] = None


class AnalyzeResponse(BaseModel):
    """Response from portfolio analysis."""

    success: bool
    analysis: Optional[PortfolioAnalysis] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

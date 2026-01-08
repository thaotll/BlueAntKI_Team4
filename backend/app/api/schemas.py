"""
API request/response schemas.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.scoring import PortfolioAnalysis


class CustomConfig(BaseModel):
    """Custom API configuration that overrides .env settings."""

    blueant_url: Optional[str] = Field(None, description="BlueAnt API base URL")
    blueant_key: Optional[str] = Field(None, description="BlueAnt API key")
    
    # Legacy Gemini config
    gemini_key: Optional[str] = Field(None, description="Gemini API key")
    
    # OpenRouter config
    openrouter_key: Optional[str] = Field(None, description="OpenRouter API key")


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
    portfolios: List[PortfolioSummary] = Field(default_factory=list)
    error: Optional[str] = None


# =============================================================================
# Analysis Endpoints
# =============================================================================


class AnalyzeRequest(BaseModel):
    """Request body for portfolio analysis."""

    portfolio_id: str = Field(..., description="BlueAnt Portfolio ID to analyze")
    custom_config: Optional[CustomConfig] = None
    
    # LLM Provider selection
    llm_provider: Optional[Literal["gemini", "openrouter"]] = Field(
        None, 
        description="LLM provider to use. Options: 'gemini', 'openrouter'. Default from config."
    )
    llm_model: Optional[str] = Field(
        None,
        description="LLM model to use. For OpenRouter, use shortnames: "
                    "devstral, gemini-flash"
    )


class AnalyzeResponse(BaseModel):
    """Response from portfolio analysis."""

    success: bool
    analysis: Optional[PortfolioAnalysis] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

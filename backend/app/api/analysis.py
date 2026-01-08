"""
Analysis API endpoints.

Supports multiple LLM providers:
- Gemini (Google)
- OpenRouter (multi-provider: Mistral, Google)
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Union

from fastapi import APIRouter

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, CustomConfig
from app.ai.gemini import GeminiError, GeminiService, get_gemini_service
from app.ai.openrouter import OpenRouterError, OpenRouterService, get_openrouter_service
from app.ai.llm_factory import get_llm_service, LLMProvider
from app.services.analyzer import PortfolioAnalyzer, LLMService
from app.services.blueant import BlueAntClientError, BlueAntService, get_blueant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])


def _get_blueant_service(custom_config: Optional[CustomConfig]) -> BlueAntService:
    """Get BlueAnt service with optional custom config."""
    if custom_config and (custom_config.blueant_url or custom_config.blueant_key):
        return BlueAntService(
            base_url=custom_config.blueant_url,
            api_key=custom_config.blueant_key,
        )
    return get_blueant_service()


def _get_llm_service(
    custom_config: Optional[CustomConfig],
    llm_provider: Optional[str],
    llm_model: Optional[str],
) -> LLMService:
    """
    Get LLM service based on configuration.
    
    Priority:
    1. Explicit llm_provider/llm_model parameters
    2. Custom config API keys
    3. Default from environment config
    """
    # Debug logging
    has_custom_config = custom_config is not None
    has_openrouter_key = bool(custom_config and custom_config.openrouter_key)
    has_gemini_key = bool(custom_config and custom_config.gemini_key)
    logger.debug(f"_get_llm_service: provider={llm_provider}, model={llm_model}, "
                 f"has_config={has_custom_config}, has_openrouter_key={has_openrouter_key}, "
                 f"has_gemini_key={has_gemini_key}")
    
    # If explicit provider is specified, use it
    if llm_provider:
        # Check for custom API keys
        if llm_provider == "openrouter":
            api_key = custom_config.openrouter_key if custom_config else None
            logger.info(f"OpenRouter selected - API key provided: {bool(api_key)}")
            if api_key:
                return OpenRouterService(api_key=api_key, model_name=llm_model)
            return get_llm_service(provider=LLMProvider.OPENROUTER, model=llm_model)
        
        elif llm_provider == "gemini":
            api_key = custom_config.gemini_key if custom_config else None
            if api_key:
                return GeminiService(api_key=api_key, model_name=llm_model)
            return get_llm_service(provider=LLMProvider.GEMINI, model=llm_model)
    
    # No explicit provider - check custom config for API keys
    if custom_config:
        if custom_config.openrouter_key:
            return OpenRouterService(api_key=custom_config.openrouter_key, model_name=llm_model)
        if custom_config.gemini_key:
            return GeminiService(api_key=custom_config.gemini_key, model_name=llm_model)
    
    # Use default configured provider
    return get_llm_service(model=llm_model)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_portfolio(request: AnalyzeRequest):
    """
    Analyze a portfolio from BlueAnt.

    This endpoint:
    1. Fetches all projects for the given portfolio from BlueAnt
    2. Normalizes the data into a consistent structure
    3. Sends data to LLM for U/I/C/R/DQ scoring (Phase 1)
    4. Generates portfolio-level analysis (Phase 2)
    5. Returns the complete analysis result
    
    Supports multiple LLM providers:
    - gemini: Google Gemini (default)
    - openrouter: OpenRouter with models like devstral, gemini-flash
    """
    start_time = datetime.now(timezone.utc)
    portfolio_id = request.portfolio_id

    # Determine provider for logging
    provider_name = request.llm_provider or "default"
    model_name = request.llm_model or "default"
    logger.info(f"Starting portfolio analysis for: {portfolio_id} (LLM: {provider_name}/{model_name})")

    try:
        # Initialize services
        blueant = _get_blueant_service(request.custom_config)
        llm_service = _get_llm_service(
            request.custom_config,
            request.llm_provider,
            request.llm_model,
        )
        analyzer = PortfolioAnalyzer(blueant, llm_service=llm_service)

        # Run analysis
        analysis = await analyzer.analyze_portfolio(portfolio_id)

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Get actual provider info
        actual_provider = type(llm_service).__name__
        actual_model = getattr(llm_service, 'model_name', 'unknown')

        logger.info(f"Analysis completed in {duration:.1f}s using {actual_provider}")

        return AnalyzeResponse(
            success=True,
            analysis=analysis,
            metadata={
                "portfolio_id": portfolio_id,
                "duration_seconds": duration,
                "project_count": len(analysis.project_scores),
                "critical_count": len(analysis.critical_projects),
                "llm_provider": actual_provider,
                "llm_model": actual_model,
                "data_warnings_count": len(analysis.data_warnings),
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
            error=f"Gemini KI-Analyse Fehler: {e}",
        )

    except OpenRouterError as e:
        logger.error(f"OpenRouter error: {e}")
        return AnalyzeResponse(
            success=False,
            error=f"OpenRouter KI-Analyse Fehler: {e}",
        )

    except ValueError as e:
        # Catches LLM configuration errors from factory
        logger.error(f"Configuration error: {e}")
        return AnalyzeResponse(
            success=False,
            error=f"Konfigurationsfehler: {e}",
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return AnalyzeResponse(
            success=False,
            error=f"Unerwarteter Fehler: {e}",
        )

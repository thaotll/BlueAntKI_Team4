"""
LLM Service Factory - Provides unified access to different LLM providers.

Supported providers:
- Gemini (Google)
- OpenRouter (multi-provider: Mistral, Google)

Usage:
    from app.ai.llm_factory import get_llm_service, LLMProvider
    
    # Use configured provider
    service = get_llm_service()
    
    # Use specific provider
    service = get_llm_service(provider=LLMProvider.OPENROUTER)
    
    # Use specific OpenRouter model
    service = get_llm_service(provider=LLMProvider.OPENROUTER, model="gemini-flash")
"""

import logging
from enum import Enum
from typing import Optional, Protocol, Union

from app.config import get_settings, OPENROUTER_MODELS
from app.models.domain import NormalizedPortfolio
from app.models.scoring import PortfolioAnalysis

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers."""
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


class LLMServiceProtocol(Protocol):
    """Protocol defining the interface for LLM services."""
    
    async def full_analysis(self, portfolio: NormalizedPortfolio) -> PortfolioAnalysis:
        """Run complete analysis on a portfolio."""
        ...


def get_llm_service(
    provider: Optional[Union[LLMProvider, str]] = None,
    model: Optional[str] = None,
) -> LLMServiceProtocol:
    """
    Factory function to get the appropriate LLM service.
    
    Args:
        provider: LLM provider to use. If None, uses configured default.
                  Options: "gemini", "openrouter"
        model: Model name or shortname to use. If None, uses configured default.
               For OpenRouter, can use shortnames: devstral, gemini-flash
    
    Returns:
        An LLM service instance (GeminiService or OpenRouterService)
    
    Raises:
        ValueError: If provider is not configured or API key is missing
    
    Examples:
        # Use default configured provider
        service = get_llm_service()
        
        # Use Gemini specifically
        service = get_llm_service(provider="gemini")
        
        # Use OpenRouter with Gemini Flash
        service = get_llm_service(provider="openrouter", model="gemini-flash")
        
        # Use OpenRouter with full model ID
        service = get_llm_service(provider="openrouter", model="mistralai/devstral-2512:free")
    """
    settings = get_settings()
    
    # Determine provider
    if provider is None:
        provider_str = settings.llm_provider
    elif isinstance(provider, LLMProvider):
        provider_str = provider.value
    else:
        provider_str = provider.lower()
    
    logger.info(f"Initializing LLM service with provider: {provider_str}")
    
    if provider_str == "openrouter":
        from app.ai.openrouter import OpenRouterService
        
        if not settings.openrouter_api_key:
            raise ValueError(
                "OpenRouter API key not configured. "
                "Set OPENROUTER_API_KEY environment variable."
            )
        
        # Resolve model shortname if provided
        model_name = model
        if model and model in OPENROUTER_MODELS:
            model_name = OPENROUTER_MODELS[model]
        elif not model:
            model_name = settings.openrouter_model
            
        logger.info(f"Using OpenRouter model: {model_name}")
        return OpenRouterService(model_name=model_name)
    
    elif provider_str == "gemini":
        from app.ai.gemini import GeminiService
        
        if not settings.gemini_api_key:
            raise ValueError(
                "Gemini API key not configured. "
                "Set GEMINI_API_KEY environment variable."
            )
        
        model_name = model or settings.gemini_model
        logger.info(f"Using Gemini model: {model_name}")
        return GeminiService(model_name=model_name)
    
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_str}. "
            f"Supported providers: gemini, openrouter"
        )


def list_available_models() -> dict:
    """
    List all available models for each provider.
    
    Returns:
        Dict with provider names as keys and model lists as values.
    """
    return {
        "gemini": [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
        "openrouter": {
            "devstral": "mistralai/devstral-2512:free",
            "gemini-flash": "google/gemini-2.0-flash-exp:free",
        },
    }


def get_provider_info() -> dict:
    """
    Get information about configured LLM providers.
    
    Returns:
        Dict with configuration status for each provider.
    """
    settings = get_settings()
    
    return {
        "configured_provider": settings.llm_provider,
        "providers": {
            "gemini": {
                "configured": bool(settings.gemini_api_key),
                "model": settings.gemini_model,
            },
            "openrouter": {
                "configured": bool(settings.openrouter_api_key),
                "model": settings.openrouter_model,
                "available_models": OPENROUTER_MODELS,
            },
        },
    }


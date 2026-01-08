"""
AI Module - LLM services for portfolio analysis.

Provides access to multiple LLM providers:
- Gemini (Google)
- OpenRouter (multi-provider: Mistral, Google)

Usage:
    from app.ai import get_llm_service, LLMProvider
    
    # Use configured provider
    service = get_llm_service()
    analysis = await service.full_analysis(portfolio)
    
    # Use specific provider
    service = get_llm_service(provider=LLMProvider.OPENROUTER, model="gemini-flash")
"""

from app.ai.llm_factory import (
    get_llm_service,
    LLMProvider,
    list_available_models,
    get_provider_info,
)
from app.ai.gemini import GeminiService, GeminiError, get_gemini_service
from app.ai.openrouter import OpenRouterService, OpenRouterError, get_openrouter_service

__all__ = [
    # Factory
    "get_llm_service",
    "LLMProvider",
    "list_available_models",
    "get_provider_info",
    # Gemini
    "GeminiService",
    "GeminiError",
    "get_gemini_service",
    # OpenRouter
    "OpenRouterService",
    "OpenRouterError",
    "get_openrouter_service",
]


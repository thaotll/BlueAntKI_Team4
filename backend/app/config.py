"""
Application configuration using pydantic-settings.
Loads values from environment variables / .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env file - check both backend dir and project root
_backend_dir = Path(__file__).parent.parent
_project_root = _backend_dir.parent
_env_file = _project_root / ".env" if (_project_root / ".env").exists() else _backend_dir / ".env"


# Available OpenRouter models (free tier)
OPENROUTER_MODELS = {
    "devstral": "mistralai/devstral-2512:free",
    "gemini-flash": "google/gemini-2.0-flash-exp:free",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_env_file),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # BlueAnt API
    blueant_base_url: str = "https://your-blueant-instance.example.com/api"
    blueant_api_key: str = ""

    # LLM Provider Selection
    # Options: "gemini", "openrouter"
    llm_provider: Literal["gemini", "openrouter"] = "gemini"

    # Gemini Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # OpenRouter Configuration
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-exp:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Optional: Your app name for OpenRouter analytics
    openrouter_app_name: str = "BlueAnt-Portfolio-Analyzer"
    openrouter_app_url: str = ""

    # ElevenLabs TTS
    elevenlabs_api_key: str = ""

    # Application
    app_env: str = "local"
    app_port: int = 8000
    log_level: str = "info"

    # CORS
    cors_origins: List[str] = ["*"]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def active_llm_api_key(self) -> str:
        """Get the API key for the currently configured LLM provider."""
        if self.llm_provider == "openrouter":
            return self.openrouter_api_key
        return self.gemini_api_key

    @property
    def active_llm_model(self) -> str:
        """Get the model name for the currently configured LLM provider."""
        if self.llm_provider == "openrouter":
            return self.openrouter_model
        return self.gemini_model

    def get_openrouter_model_id(self, shortname: Optional[str] = None) -> str:
        """
        Get full OpenRouter model ID from shortname or return configured model.
        
        Shortnames: devstral, gemini-flash
        """
        if shortname and shortname in OPENROUTER_MODELS:
            return OPENROUTER_MODELS[shortname]
        return self.openrouter_model


@lru_cache
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Use dependency injection in FastAPI routes.
    """
    return Settings()

"""
Application configuration using pydantic-settings.
Loads values from environment variables / .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env file - check both backend dir and project root
_backend_dir = Path(__file__).parent.parent
_project_root = _backend_dir.parent
_env_file = _project_root / ".env" if (_project_root / ".env").exists() else _backend_dir / ".env"


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

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Application
    app_env: str = "local"
    app_port: int = 8000
    log_level: str = "info"

    # CORS
    cors_origins: List[str] = ["*"]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Use dependency injection in FastAPI routes.
    """
    return Settings()

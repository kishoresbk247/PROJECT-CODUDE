"""
CoDude Configuration
Loads environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    OPENAI_API_KEY: str = "sk-placeholder"
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance — import this across modules
settings = Settings()

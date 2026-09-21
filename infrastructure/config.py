"""Configuration settings for AI Company OS."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Company OS"
    app_env: str = "development"
    app_version: str = "0.1.0"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # PostgreSQL database URLs
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_company_os"
    sync_database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_company_os"

    # Redis URL
    redis_url: str = "redis://localhost:6379/0"

    # Authentication & Session Settings
    session_expire_days: int = 7
    session_cookie_name: str = "ai_company_session"
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 900
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()

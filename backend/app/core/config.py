"""
Application Configuration — pydantic-settings
All values read from environment variables / .env file.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────
    APP_NAME: str = "Product Price Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ──────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./price_tracker.db"
    DATABASE_URL_SYNC: str = "sqlite:///./price_tracker.db"

    # ── Redis ─────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── CORS ──────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "*",
    ]

    # ── Email ─────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    EMAILS_FROM_NAME: str = "Price Tracker"

    # ── Scraper ───────────────────────────────────────
    SCRAPER_TIMEOUT: int = 30          # seconds
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_RETRY_DELAY: int = 5       # seconds

    # ── Scheduler ─────────────────────────────────────
    DEFAULT_SCRAPE_INTERVAL_MINUTES: int = 60

    # ── ML ────────────────────────────────────────────
    ML_MODELS_DIR: str = "ml_models"
    MIN_HISTORY_POINTS: int = 5        # Minimum data points for ML


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()

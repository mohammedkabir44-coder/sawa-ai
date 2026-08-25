"""Application configuration loaded from environment variables.

Secrets are never hard-coded. All values come from the environment or
the local `.env` file (see `.env.example`).
"""
from functools import lru_cache
from typing import Annotated, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core ---
    APP_NAME: str = "SAWA AI"
    APP_ENV: str = "development"  # development | production
    ENVIRONMENT: str = "development"  # development | production (alias for APP_ENV)
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    TIMEZONE: str = "Africa/Lagos"
    DEFAULT_CURRENCY: str = "NGN"

    # --- Security ---
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- Database ---
    # Default is a clearly-marked local SQLite fallback for development.
    # In production set DATABASE_URL to a PostgreSQL (e.g. Neon) URL.
    DATABASE_URL: str = "sqlite:///./sawa_dev.db"

    # --- CORS ---
    # NoDecode prevents pydantic-settings from trying to JSON-decode the
    # value from the environment; the validator splits it (and tolerates
    # bracketed forms like '["http://localhost:5173"]').
    CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1]
            return [
                o.strip().strip('"').strip("'")
                for o in s.split(",")
                if o.strip()
            ]
        return v

    # --- Provider selection (controlled by env) ---
    AI_PROVIDER: str = "mock"  # mock | gemini
    WHATSAPP_PROVIDER: str = "mock"  # mock | meta
    SMS_PROVIDER: str = "mock"  # mock | nigerian
    SPEECH_PROVIDER: str = "mock"  # mock | gemini

    # --- Secrets (never exposed to frontend) ---
    GEMINI_API_KEY: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "sawatoken123"
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_API_KEY_ENCRYPTION_KEY: str = ""
    SMS_API_KEY: str = ""
    SMS_API_SECRET: str = ""
    SMS_SENDER_ID: str = "SAWA"

    # --- Background jobs ---
    JOB_POLL_INTERVAL_SECONDS: int = 5

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
"""Application configuration via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # app
    APP_NAME: str = "TrustScan"
    APP_VERSION: str = "4.2.0"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # security
    SECRET_KEY: str = "change-me-in-production-" + "x" * 32
    JWT_ALG: str = "HS256"
    JWT_ACCESS_TTL_MIN: int = 30
    JWT_REFRESH_TTL_DAYS: int = 30
    OTP_TTL_SECONDS: int = 300
    OTP_RESEND_COOLDOWN_SEC: int = 60
    OTP_MAX_ATTEMPTS: int = 5
    OTP_LENGTH: int = 6

    # cors
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # database
    DATABASE_URL: str = "sqlite+aiosqlite:///./trustscan.db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # cache
    REDIS_URL: Optional[str] = None
    CACHE_SCAN_TTL: int = 300
    CACHE_REPUTATION_TTL: int = 1800
    CACHE_DNS_TTL: int = 600
    CACHE_AI_TTL: int = 3600

    # rate limiting
    RATE_LIMIT_SCAN_PER_MIN: int = 30
    RATE_LIMIT_AUTH_PER_MIN: int = 10
    RATE_LIMIT_GLOBAL_PER_MIN: int = 120

    # http client
    HTTP_TIMEOUT: float = 10.0
    HTTP_MAX_REDIRECTS: int = 5
    HTTP_USER_AGENT: str = (
        "Mozilla/5.0 (compatible; TrustScan/4.2; +https://trustscan.ai/bot)"
    )

    # intelligence providers (all free tiers)
    GOOGLE_SAFE_BROWSING_API_KEY: Optional[str] = None
    ABUSEIPDB_API_KEY: Optional[str] = None
    IPQS_API_KEY: Optional[str] = None

    # AI providers — free only
    # Puter.js relays Claude Sonnet for free using a browser auth token.
    PUTER_AUTH_TOKEN: Optional[str] = None
    AI_MODEL_CLAUDE: str = "claude-sonnet-4-5"

    # email / smtp
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "TrustScan <noreply@trustscan.ai>"
    SMTP_TLS: bool = True

    # scanner safety
    BLOCK_PRIVATE_IPS: bool = True
    BLOCK_LOCALHOST: bool = True
    ALLOWED_SCHEMES: List[str] = ["http", "https"]
    MAX_URL_LENGTH: int = 2048
    MAX_REDIRECT_CHAIN: int = 10

    # logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    METRICS_ENABLED: bool = True

    @field_validator("CORS_ORIGINS", "ALLOWED_SCHEMES", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

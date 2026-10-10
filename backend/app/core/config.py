"""Application Configuration via Pydantic Settings."""

import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General App Config
    APP_NAME: str = "Cross-Border E-Commerce Pricing Intelligence"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./pricing_intelligence.db"

    # Foreign Exchange Rate API
    FX_API_URL: str = "https://open.er-api.com/v6/latest/USD"
    FX_CACHE_TTL_HOURS: int = 12

    # Web Scraping Configuration
    SCRAPER_REQUEST_TIMEOUT: int = 15
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_RATE_LIMIT_DELAY_MIN: float = 1.0
    SCRAPER_RATE_LIMIT_DELAY_MAX: float = 2.5
    SCRAPER_MAX_CONCURRENT_REQUESTS: int = 5

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # 'console' or 'json'


settings = Settings()

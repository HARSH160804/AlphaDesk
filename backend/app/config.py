"""Runtime configuration, loaded from environment variables / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_PATH = REPO_ROOT / "data" / "alphadesk.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    risk_free_rate: float = Field(default=0.065, alias="RISK_FREE_RATE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    mfapi_base_url: str = Field(default="https://api.mfapi.in/mf", alias="MFAPI_BASE_URL")
    mfapi_request_delay_ms: int = Field(default=250, alias="MFAPI_REQUEST_DELAY_MS")
    mfapi_max_retries: int = Field(default=4, alias="MFAPI_MAX_RETRIES")
    ingest_max_workers: int = Field(default=4, alias="INGEST_MAX_WORKERS")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"

    @property
    def funds_config_path(self) -> Path:
        return REPO_ROOT / "config" / "funds.yaml"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

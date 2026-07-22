from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(extra="ignore")

    postgres_user: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    postgres_password: str | None = Field(default=None, validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="backend-db", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="PGPORT")
    postgres_db: str = Field(default="test", validation_alias="POSTGRES_DB")
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")

    celery_broker_url: str = Field(
        default="redis://backend-redis:6379/0",
        validation_alias="CELERY_BROKER_URL",
    )
    celery_result_backend: str | None = Field(
        default=None,
        validation_alias="CELERY_RESULT_BACKEND",
    )
    storage_dir: Path = Field(
        default=BACKEND_DIR / "storage" / "files",
        validation_alias="STORAGE_DIR",
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        user = quote(self.postgres_user, safe="")
        credentials = user
        if self.postgres_password:
            credentials = f"{user}:{quote(self.postgres_password, safe='')}"
        return (
            f"postgresql+asyncpg://{credentials}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.celery_broker_url

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

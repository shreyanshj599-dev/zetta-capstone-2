from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "zetta"
    postgres_password: str = "zetta"
    postgres_db: str = "zetta"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    render_database_url: str | None = Field(default=None, alias="DATABASE_URL")

    redis_url: str = "redis://redis:6379/0"
    company_cache_ttl_seconds: int = 86400

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    celery_worker_pool: str = "threads"
    celery_worker_concurrency: int = 4

    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        if self.render_database_url:
            return self.render_database_url.replace("postgresql://", "postgresql+psycopg://", 1)

        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

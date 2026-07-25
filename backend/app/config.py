from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TraceFrame"
    app_env: str = "development"
    database_path: Path = Path("data/traceframe.db")
    artifacts_path: Path = Path("data/artifacts")
    openai_api_key: str | None = None
    openai_image_model: str = "gpt-image-1"
    b2_key_id: str | None = None
    b2_app_key: str | None = None
    b2_bucket: str | None = None
    b2_region: str = "us-west-004"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    demo_mode: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @property
    def live_ready(self) -> bool:
        return bool(self.openai_api_key and self.b2_key_id and self.b2_app_key and self.b2_bucket)


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings, loaded from environment variables (or backend/.env locally)."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    supabase_url: str = ""
    supabase_key: str = ""
    app_timezone: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    return Settings()

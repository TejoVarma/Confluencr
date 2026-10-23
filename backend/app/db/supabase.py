from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings
from app.core.errors import AppError


@lru_cache
def _create_client(url: str, key: str) -> Client:
    return create_client(url, key)


def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise AppError("Database is not configured", 503)
    return _create_client(settings.supabase_url, settings.supabase_key)

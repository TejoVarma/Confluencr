from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def today() -> date:
    """Current date in the configured app timezone."""
    return datetime.now(ZoneInfo(get_settings().app_timezone)).date()

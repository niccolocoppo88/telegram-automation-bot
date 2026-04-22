"""Utility helpers."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def format_timestamp(dt: datetime | None = None) -> str:
    """Format datetime as ISO string."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_int(value: str | int | None, default: int = 0) -> int:
    """Safely convert value to int."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_admin_ids(value: str | list[int] | None) -> list[int]:
    """Parse admin user IDs from string or list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [safe_int(x.strip()) for x in value.split(",") if x.strip()]
    return []

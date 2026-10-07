"""
Database Timestamp Utilities.
Provides standard UTC datetime generation, timezone coercion, and serialization helpers.
"""

from datetime import datetime, timezone
from typing import Optional, Union


def now_utc() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[Union[datetime, str]]) -> Optional[datetime]:
    """
    Ensures a datetime object is timezone-aware UTC.
    Parses ISO strings if string datetime input is provided.

    Args:
        dt: Datetime object or ISO formatted datetime string.

    Returns:
        Optional[datetime]: UTC aware datetime or None.
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """Formats datetime object to standard ISO-8601 string."""
    if dt is None:
        return None
    utc_dt = ensure_utc(dt)
    return utc_dt.isoformat() if utc_dt else None

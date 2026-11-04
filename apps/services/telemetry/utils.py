from datetime import datetime, timezone


def _ensure_utc(dt: datetime) -> datetime:
    """Naive datetime считаем UTC; aware — приводим к UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

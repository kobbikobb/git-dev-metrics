import re
from datetime import UTC, datetime, timedelta


def parse_time_period(event_period: str) -> datetime:
    """Parse time period string and return the start date."""
    match = re.match(r"(\d+)(d|w|m)", event_period)
    if match:
        value, unit = match.groups()
        if unit == "m" and value == "1":
            return _start_of_last_calendar_month()
        days = int(value)
        if unit == "w":
            days *= 7
        elif unit == "m":
            days *= 30
        return datetime.now(UTC) - timedelta(days=days)

    period_map = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "180d": timedelta(days=180),
    }

    delta = period_map.get(event_period, timedelta(days=30))

    return datetime.now(UTC) - delta


def _start_of_last_calendar_month() -> datetime:
    """Return 00:00:00 UTC on the 1st day of the previous calendar month."""
    today = datetime.now(UTC)
    first_of_current = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_prev_month = first_of_current - timedelta(days=1)
    return last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_period_display_name(period: str) -> str:
    """Convert period string to human-readable display name."""
    if period == "1m":
        today = datetime.now(UTC)
        first_of_current = today.replace(day=1)
        last_day_prev = first_of_current - timedelta(days=1)
        return last_day_prev.strftime("%B %Y")
    return f"Last {period}"

import re
from datetime import UTC, datetime, timedelta


def parse_time_period(event_period: str) -> tuple[datetime, datetime]:
    """Parse time period string and return (start, end) datetimes.

    End is always current time. Start is calculated based on the period.
    """
    now = datetime.now(UTC)
    match = re.match(r"(\d+)(d|w|m)", event_period)
    if match:
        value, unit = match.groups()
        if unit == "m" and value == "1":
            return _last_calendar_month_range()
        days = int(value)
        if unit == "w":
            days *= 7
        elif unit == "m":
            days *= 30
        return (now - timedelta(days=days), now)

    period_map = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "180d": timedelta(days=180),
    }

    delta = period_map.get(event_period, timedelta(days=30))

    return (now - delta, now)


def _last_calendar_month_range() -> tuple[datetime, datetime]:
    """Return (start, end) of the previous calendar month."""
    now = datetime.now(UTC)
    first_of_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_prev_month = first_of_current - timedelta(days=1)
    start = last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = last_day_prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)
    return (start, end)


def get_period_display_name(period: str) -> str:
    """Convert period string to human-readable display name."""
    if period == "1m":
        start, _ = _last_calendar_month_range()
        return start.strftime("%B %Y")
    return f"Last {period}"

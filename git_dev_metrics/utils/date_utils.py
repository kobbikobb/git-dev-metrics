import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class TimePeriod:
    since: datetime
    until: datetime

    def __post_init__(self):
        if self.since > self.until:
            raise ValueError("since must be before until.")


def month_range(year: int, month: int) -> TimePeriod:
    """TimePeriod covering the calendar month [first 00:00 UTC, first of next 00:00 UTC)."""
    if not 1 <= month <= 12:
        raise ValueError(f"Unsupported period: {year:04d}-{month:02d}")
    since = datetime(year, month, 1, tzinfo=UTC)
    until = datetime(year + (month // 12), (month % 12) + 1, 1, tzinfo=UTC)
    return TimePeriod(since=since, until=until)


def get_last_month() -> TimePeriod:
    """Gets the TimePeriod for last month"""
    now = datetime.now(UTC)
    year, month = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    return month_range(year, month)


_YEAR_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def parse_time_period(event_period: str) -> TimePeriod:
    """Parse time period string and return a TimePeriod."""
    if event_period == "last_month":
        return get_last_month()

    if m := _YEAR_MONTH_RE.match(event_period):
        return month_range(int(m.group(1)), int(m.group(2)))

    period_map = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "180d": timedelta(days=180),
    }
    if event_period not in period_map:
        raise ValueError(f"Unsupported period: {event_period}")

    now = datetime.now(UTC)
    return TimePeriod(since=now - period_map[event_period], until=now)

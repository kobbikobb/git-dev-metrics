from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class TimePeriod:
    since: datetime
    until: datetime

    def __post_init__(self):
        if self.since > self.until:
            raise ValueError("since must be before until.")


def get_last_month() -> TimePeriod:
    """Gets the TimePeriod for last month"""
    now = datetime.now(UTC)

    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    since = (first_of_this_month - timedelta(days=1)).replace(day=1)
    until = first_of_this_month

    return TimePeriod(since=since, until=until)


def parse_time_period(event_period: str) -> TimePeriod:
    """Parse time period string and return a TimePeriod."""
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

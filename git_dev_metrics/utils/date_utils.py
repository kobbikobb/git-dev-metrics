import re
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class TimePeriod:
    since: datetime
    until: datetime

    def __post_init__(self):
        if self.since > self.until:
            raise ValueError("since must be before until.")


def period_days(period: TimePeriod) -> int:
    """Whole days spanned by the TimePeriod (min 1). Source of truth for prs_per_week."""
    return max(1, round((period.until - period.since).total_seconds() / 86400))


def month_range(year: int, month: int) -> TimePeriod:
    """TimePeriod covering the calendar month [first 00:00 UTC, first of next 00:00 UTC)."""
    if not 1 <= month <= 12:
        raise ValueError(f"Unsupported period: {year:04d}-{month:02d}")
    since = datetime(year, month, 1, tzinfo=UTC)
    until = datetime(year + (month // 12), (month % 12) + 1, 1, tzinfo=UTC)
    return TimePeriod(since=since, until=until)


def month_iter(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """Inclusive list of (year, month) tuples from start to end in chronological order."""
    out: list[tuple[int, int]] = []
    y, m = start
    while (y, m) <= end:
        out.append((y, m))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


def range_period(start: tuple[int, int], end: tuple[int, int]) -> TimePeriod:
    """TimePeriod from start month's first day to end month's first-of-next-month."""
    since = month_range(*start).since
    until = month_range(*end).until
    return TimePeriod(since=since, until=until)


def get_last_month() -> TimePeriod:
    """Gets the TimePeriod for last month"""
    now = datetime.now(UTC)
    year, month = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    return month_range(year, month)


_YEAR_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def parse_iso_datetime(dt_str: str | None) -> datetime | None:
    """Parse ISO-8601 datetime string to datetime. Returns None for falsy or malformed input."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_year_month(value: str) -> tuple[int, int]:
    """Parse "YYYY-MM" into (year, month). Raises ValueError on malformed input."""
    m = _YEAR_MONTH_RE.match(value)
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise ValueError(f"Expected YYYY-MM, got {value!r}")
    return int(m.group(1)), int(m.group(2))


def format_date_range(period: TimePeriod) -> str:
    since = period.since.strftime("%Y-%m-%d")
    until = period.until.strftime("%Y-%m-%d")
    return f"{since} to {until}"

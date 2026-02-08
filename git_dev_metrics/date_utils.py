from datetime import datetime, timedelta


def parse_time_period(event_period: str) -> datetime:
    """Parse time period string and return the start date."""
    period_map = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }

    delta = period_map.get(event_period, timedelta(days=30))
    return datetime.now() - delta

from ...metrics import MetricsSnapshot


def format_period_slug(a: str, b: str) -> str:
    return f"{a}-to-{b}"


def format_date_range(snapshot: MetricsSnapshot) -> str:
    since = snapshot.period.since.strftime("%Y-%m-%d")
    until = snapshot.period.until.strftime("%Y-%m-%d")
    return f"{since} to {until}"

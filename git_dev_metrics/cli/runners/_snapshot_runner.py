from ...metrics import MetricsSnapshot

YearMonth = tuple[int, int]


def format_period_slug(
    selected: list[YearMonth] | None = None,
    flag_from: str | None = None,
    flag_to: str | None = None,
) -> str:
    if selected:
        first, last = selected[0], selected[-1]
        return f"{first[0]:04d}-{first[1]:02d}-to-{last[0]:04d}-{last[1]:02d}"
    return f"{flag_from}-to-{flag_to}"


def format_date_range(snapshot: MetricsSnapshot) -> str:
    since = snapshot.period.since.strftime("%Y-%m-%d")
    until = snapshot.period.until.strftime("%Y-%m-%d")
    return f"{since} to {until}"

from ...utils.date_utils import TimePeriod


def format_date_range(period: TimePeriod) -> str:
    since = period.since.strftime("%Y-%m-%d")
    until = period.until.strftime("%Y-%m-%d")
    return f"{since} to {until}"

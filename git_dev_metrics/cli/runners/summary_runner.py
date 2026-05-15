from ...metrics import MetricsSnapshot
from ...metrics.printer import ConsolePrinter
from ._snapshot_runner import YearMonth, format_date_range, format_period_slug


def print_console_summary(
    snapshot: MetricsSnapshot,
    *,
    selected: list[YearMonth] | None = None,
    flag_from: str | None = None,
    flag_to: str | None = None,
) -> None:
    period_slug = format_period_slug(selected=selected, flag_from=flag_from, flag_to=flag_to)
    ConsolePrinter().print_combined_metrics(snapshot, period_slug, format_date_range(snapshot))

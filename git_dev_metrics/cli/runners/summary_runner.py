from ...metrics import MetricsSnapshot
from ...metrics.printer import ConsolePrinter


def print_console_summary(snapshot: MetricsSnapshot, period_slug: str, date_range: str) -> None:
    ConsolePrinter().print_combined_metrics(snapshot, period_slug, date_range)

from datetime import datetime
from pathlib import Path

import typer

from ...metrics import MetricsSnapshot
from ...metrics.printer.html import FileHtmlPrinter
from .._browser import open_in_browser
from ._snapshot_runner import YearMonth, format_date_range, format_period_slug


def _default_output(period_slug: str) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path(f"./metrics_results/dashboard_{ts}_{period_slug}.html")


def write_and_open_dashboard(
    snapshot: MetricsSnapshot,
    output: Path | None,
    *,
    selected: list[YearMonth] | None = None,
    flag_from: str | None = None,
    flag_to: str | None = None,
) -> None:
    period_slug = format_period_slug(selected=selected, flag_from=flag_from, flag_to=flag_to)
    out = (output or _default_output(period_slug)).with_suffix(".html")
    FileHtmlPrinter(out).print_combined_metrics(snapshot, period_slug, format_date_range(snapshot))
    typer.echo(f"Dashboard written to {out}.")
    open_in_browser(out)

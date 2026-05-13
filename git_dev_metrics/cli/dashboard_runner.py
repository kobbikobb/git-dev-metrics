from datetime import datetime
from pathlib import Path

import typer

from ..metrics.printer.html import FileHtmlPrinter
from ._browser import open_in_browser


def _default_output(period_slug: str) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path(f"./metrics_results/dashboard_{ts}_{period_slug}.html")


def write_and_open_dashboard(
    metrics: dict, period_slug: str, date_range: str, output: Path | None
) -> None:
    out = (output or _default_output(period_slug)).with_suffix(".html")
    FileHtmlPrinter(out).print_combined_metrics(metrics, period_slug, date_range)
    typer.echo(f"Dashboard written to {out}.")
    open_in_browser(out)

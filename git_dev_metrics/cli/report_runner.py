from pathlib import Path

from ..metrics.printer import ConsolePrinter, FilePrinter, get_default_output_path
from ..metrics.printer.html import FileHtmlPrinter
from ._browser import open_in_browser


def render_combined(
    metrics: dict,
    period_slug: str,
    date_range: str,
    output: Path | None,
    open_browser: bool = True,
) -> None:
    """Render the MD + HTML + console dashboard for a month's metrics."""
    if output is None:
        default_md = get_default_output_path(period_slug)
        ConsolePrinter().print_combined_metrics(metrics, period_slug, date_range)
        FilePrinter(default_md).print_combined_metrics(metrics, period_slug, date_range)
        FileHtmlPrinter(default_md).print_combined_metrics(metrics, period_slug, date_range)
        if open_browser:
            open_in_browser(default_md.with_suffix(".html"))
        return

    if output.suffix.lower() == ".html":
        FileHtmlPrinter(output).print_combined_metrics(metrics, period_slug, date_range)
        if open_browser:
            open_in_browser(output)
    else:
        FilePrinter(output).print_combined_metrics(metrics, period_slug, date_range)

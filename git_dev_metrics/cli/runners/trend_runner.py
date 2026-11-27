from pathlib import Path

import typer

from ...metrics.printer.trend import FileTrendPrinter
from ...metrics.report_data import ReportData
from ...utils.date_utils import month_iter
from .._browser import open_in_browser

YearMonth = tuple[int, int]


def _default_output(from_ym: YearMonth, to_ym: YearMonth) -> Path:
    return Path(
        f"./metrics_results/trend_"
        f"{from_ym[0]:04d}-{from_ym[1]:02d}_{to_ym[0]:04d}-{to_ym[1]:02d}.html"
    )


def perform_trend(
    from_ym: YearMonth,
    to_ym: YearMonth,
    output: Path | None,
    db_path: Path | None,
) -> None:
    """Validate range, aggregate PRs across every cached repo, render HTML, open browser."""
    if to_ym < from_ym:
        typer.secho("--to must be >= --from.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    months = month_iter(from_ym, to_ym)
    dataset = ReportData(db_path).trend(months)
    if dataset is None:
        typer.secho(
            "No synced data for selected range. Run pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    out_path = output or _default_output(from_ym, to_ym)
    FileTrendPrinter(out_path).render(dataset)
    typer.echo(f"Trend written to {out_path}.")
    open_in_browser(out_path)

import webbrowser
from pathlib import Path

import typer

from ...cache import load_all_repos_by_month
from ...metrics.printer.trend import FileTrendPrinter
from ...metrics.trend_calculator import build_trend_dataset
from ...utils.date_utils import month_iter

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
    prs_per_month = load_all_repos_by_month(months, db_path=db_path)
    if not any(prs_per_month.values()):
        typer.secho(
            "No synced data for selected range. Run pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    dataset = build_trend_dataset(months, prs_per_month)
    out_path = output or _default_output(from_ym, to_ym)
    FileTrendPrinter(out_path).render(dataset)
    typer.echo(f"Trend written to {out_path}.")
    webbrowser.open(out_path.resolve().as_uri())

from datetime import datetime
from pathlib import Path

import typer

from ..cache import is_sealed, load_prs_for_range
from ..metrics.printer.trend import FileTrendPrinter
from ..metrics.trend_calculator import build_trend_dataset
from ..utils.date_utils import month_iter

YearMonth = tuple[int, int]


def _default_output(org: str, repo: str, from_ym: YearMonth, to_ym: YearMonth) -> Path:
    return Path(
        f"./metrics_results/trend_{org}-{repo}_"
        f"{from_ym[0]:04d}-{from_ym[1]:02d}_{to_ym[0]:04d}-{to_ym[1]:02d}.html"
    )


def perform_trend(
    org: str,
    repo: str,
    from_ym: YearMonth,
    to_ym: YearMonth,
    output: Path | None,
    db_path: Path | None,
) -> None:
    """Shared core: validate range, verify each month sealed, build dataset, render HTML."""
    if to_ym < from_ym:
        typer.secho("--to must be >= --from.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    months = month_iter(from_ym, to_ym)
    for year, month in months:
        if not is_sealed(org, repo, year, month, db_path=db_path):
            label = datetime(year, month, 1).strftime("%b %Y")
            typer.secho(f"{label} not sealed", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    prs_per_month = load_prs_for_range(org, repo, months, db_path=db_path)
    dataset = build_trend_dataset(months, prs_per_month)

    out_path = output or _default_output(org, repo, from_ym, to_ym)
    FileTrendPrinter(out_path).render(dataset, org, repo)
    typer.echo(f"Trend written to {out_path}.")

from datetime import datetime
from pathlib import Path

import typer

from ...cache import load_all_repos_by_month
from ...metrics.printer.team_velocity import FileTeamVelocityPrinter
from ...metrics.team_velocity_calculator import build_team_velocity_dataset
from ...utils.date_utils import month_iter
from .._browser import open_in_browser

YearMonth = tuple[int, int]


def _default_output(from_ym: YearMonth, to_ym: YearMonth) -> Path:
    return Path(
        f"./metrics_results/team_velocity_"
        f"{from_ym[0]:04d}-{from_ym[1]:02d}_{to_ym[0]:04d}-{to_ym[1]:02d}.html"
    )


def perform_team_velocity(
    from_ym: YearMonth,
    to_ym: YearMonth,
    output: Path | None,
    db_path: Path | None,
) -> None:
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

    dataset = build_team_velocity_dataset(months, prs_per_month)
    first, last = months[0], months[-1]
    period_range = (
        f"{datetime(first[0], first[1], 1).strftime('%b %Y')}"
        f" – {datetime(last[0], last[1], 1).strftime('%b %Y')}"
    )
    out_path = output or _default_output(from_ym, to_ym)
    FileTeamVelocityPrinter(out_path).render(dataset, period_range)
    typer.echo(f"Team velocity written to {out_path}.")
    open_in_browser(out_path)

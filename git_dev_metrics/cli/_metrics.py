from pathlib import Path

import typer

from ..cache import load_all_repos_for_range
from ..metrics import MetricsSnapshot
from ..utils.date_utils import month_iter, range_period
from ._month_arg import parse_month_arg

_DATE_FMT = "%Y-%m-%d"

YearMonth = tuple[int, int]


def _slug(ym: YearMonth) -> str:
    return f"{ym[0]:04d}-{ym[1]:02d}"


def metrics_for_months(
    months: list[YearMonth], db_path: Path | None
) -> tuple[MetricsSnapshot, str, str] | None:
    repo_prs = load_all_repos_for_range(months, db_path=db_path)
    if not repo_prs:
        return None
    period = range_period(months[0], months[-1])
    snapshot = MetricsSnapshot.from_repo_prs(repo_prs, period)
    period_slug = f"{_slug(months[0])}-to-{_slug(months[-1])}"
    date_range = f"{period.since.strftime(_DATE_FMT)} to {period.until.strftime(_DATE_FMT)}"
    return snapshot, period_slug, date_range


def metrics_for_range(from_: str, to: str, db: Path | None) -> tuple[MetricsSnapshot, str, str]:
    from_ym = parse_month_arg(from_, "--from")
    to_ym = parse_month_arg(to, "--to")
    if to_ym < from_ym:
        typer.secho("--to must be >= --from.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    months = month_iter(from_ym, to_ym)
    result = metrics_for_months(months, db)
    if result is None:
        typer.secho(
            f"No synced data for {from_} to {to}. Run pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    return result

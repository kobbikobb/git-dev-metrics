from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import typer

from ..cache import insert_prs, is_sealed, seal_month
from ..github import get_github_token
from ..github.queries import fetch_repo_metrics
from ..models import PullRequest
from ..utils.date_utils import month_range, parse_year_month, TimePeriod
from .pull_wizard import pull_wizard


def _parse_month_arg(value: str, flag: str = "--month") -> tuple[int, int]:
    """Parse a YYYY-MM CLI argument, exiting with a typer-styled error on bad input."""
    try:
        return parse_year_month(value)
    except ValueError as e:
        typer.secho(f"Invalid {flag} '{value}'; expected YYYY-MM.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


def _fetch_and_seal_month(
    org: str,
    repo: str,
    year: int,
    month: int,
    period: TimePeriod,
    token: str,
    db_path: Path | None,
    fetch: Callable[..., list[PullRequest]] | None = None,
) -> int:
    """Fetch a month of PRs for one repo, upsert into the cache, seal it, return PR count."""
    prs = (fetch or fetch_repo_metrics)(token, org, repo, period)
    insert_prs(prs, org, repo, year, month, db_path=db_path)
    seal_month(org, repo, year, month, db_path=db_path)
    return len(prs)


def pull(
    month: str | None = typer.Option(None, "--month", help="Month to pull, YYYY-MM"),
    org: str | None = typer.Option(None, "--org", help="GitHub organization or user"),
    repo: str | None = typer.Option(None, "--repo", help="GitHub repository name"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Pull a sealed month of PRs for one repository into the cache."""
    if month is None and org is None and repo is None:
        pull_wizard(db_path=db)
        return

    if month is None or org is None or repo is None:
        typer.secho(
            "Provide all of --month, --org and --repo, or none (for the wizard).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    year, month_num = _parse_month_arg(month)
    period = month_range(year, month_num)

    if period.until > datetime.now(UTC):
        typer.secho(f"Month {month} is incomplete; cannot seal.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if is_sealed(org, repo, year, month_num, db_path=db):
        typer.secho(
            f"Month {month} for {org}/{repo} is already sealed.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    token = get_github_token()
    n = _fetch_and_seal_month(org, repo, year, month_num, period, token, db)

    typer.echo(f"Pulled {n} PRs for {org}/{repo} {month}.")

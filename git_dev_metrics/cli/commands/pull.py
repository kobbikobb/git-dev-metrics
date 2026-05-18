from datetime import UTC, datetime
from pathlib import Path

import typer

from ...cache import is_sealed
from ...github import get_github_token
from ...utils.date_utils import month_range, parse_year_month
from ..runners.pull_runner import fetch_and_seal_month
from ..wizards.pull_wizard import pull_wizard


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

    try:
        year, month_num = parse_year_month(month)
    except ValueError as e:
        typer.secho(f"Invalid --month '{month}'; expected YYYY-MM.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e
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
    n = fetch_and_seal_month(org, repo, year, month_num, period, token, db)

    typer.echo(f"Pulled {n} PRs for {org}/{repo} {month}.")

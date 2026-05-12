from pathlib import Path

import typer

from ._month_arg import parse_month_arg
from .trend_runner import perform_trend
from .trend_wizard import trend_wizard


def trend(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    org: str | None = typer.Option(None, "--org", help="GitHub organization or user"),
    repo: str | None = typer.Option(None, "--repo", help="GitHub repository name"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Render a multi-month trend HTML for one repository."""
    if from_ is None and to is None and org is None and repo is None:
        trend_wizard(db_path=db)
        return

    if from_ is None or to is None or org is None or repo is None:
        typer.secho(
            "Provide all of --from, --to, --org and --repo, or none (for the wizard).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    from_ym = parse_month_arg(from_, "--from")
    to_ym = parse_month_arg(to, "--to")
    perform_trend(org, repo, from_ym, to_ym, output=output, db_path=db)

import logging
from pathlib import Path

import typer

from .runner import AnalysisError, run_analyze
from .validation import validate_period

logger = logging.getLogger(__name__)


def analyze(
    org: str | None = typer.Option(None, help="GitHub organization name"),
    repo: str | None = typer.Option(None, help="Repository name"),
    period: str = typer.Option(
        "30d", callback=validate_period, help="Time period (e.g. 7d, 30d, 90d)"
    ),
    output: Path | None = typer.Option(None, help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full error tracebacks"),
) -> None:
    """
    Analyze GitHub repository development metrics.

    If --org and --repo are omitted, you will be prompted to select
    from your recently active repositories.
    """
    from .validation import validate_org_repo_pair

    validate_org_repo_pair(org, repo)

    typer.secho("Configuring GitHub Auth Token...", fg=typer.colors.BRIGHT_YELLOW, bold=True)

    try:
        run_analyze(
            org=org,
            repo=repo,
            period=period,
            output_path=str(output) if output else None,
            verbose=verbose,
        )
    except AnalysisError as e:
        typer.secho(f"Analysis failed: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1) from e

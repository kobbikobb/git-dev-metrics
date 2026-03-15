import logging
from pathlib import Path

import typer

from .runner import AnalysisError, run_analyze

logger = logging.getLogger(__name__)


def analyze(
    org: str | None = typer.Option(None, "--org", help="GitHub organization or user"),
    repo: str | None = typer.Option(None, "--repo", help="GitHub repository name"),
    period: str | None = typer.Option(None, "--period", help="Time period (e.g., 30d, 7d, 90d)"),
    output: Path | None = typer.Option(None, help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full error tracebacks"),
    log_level: str = typer.Option(
        "WARNING", "--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR)"
    ),
) -> None:
    """Analyze GitHub repository development metrics."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.WARNING),
        format="%(levelname)s: %(message)s",
    )
    try:
        run_analyze(output=output, org=org, repo=repo, period=period)
    except AnalysisError as e:
        logger.error("Analysis failed: %s", e)
        if verbose:
            logger.exception("Full traceback:")
        typer.secho(f"Analysis failed: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1) from e

import logging
from pathlib import Path

import typer

from .runner import AnalysisError, run_analyze

logger = logging.getLogger(__name__)


def analyze(
    output: Path | None = typer.Option(None, help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full error tracebacks"),
) -> None:
    """Analyze GitHub repository development metrics."""
    try:
        run_analyze(output=output)
    except AnalysisError as e:
        logger.error("Analysis failed: %s", e)
        if verbose:
            logger.exception("Full traceback:")
        typer.secho(f"Analysis failed: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1) from e

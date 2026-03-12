import logging
from pathlib import Path

import typer

from ..github import GitHubError, get_github_token
from ..metrics import get_combined_metrics, get_recent_repositories
from ..metrics.printer import CompositePrinter, get_default_output_path
from .prompts import prompt_repo_selection
from .validation import validate_period

logger = logging.getLogger(__name__)
app = typer.Typer()


def _resolve_output_path(output: Path | None) -> Path:
    """Resolve output path from user input or return default."""
    return output if output else get_default_output_path()


def _print_metrics(metrics: dict, period: str, output_path: Path) -> None:
    """Print metrics to the specified output path."""
    CompositePrinter(output_path).print_combined_metrics(metrics, period)
    typer.secho(f"Results saved to {output_path}", fg=typer.colors.GREEN)


def _validate_org_repo_pair(org: str | None, repo: str | None) -> None:
    """Ensure org and repo are either both provided or both omitted."""
    if (org is None) != (repo is None):
        raise typer.BadParameter("Both --org and --repo must be provided together, or neither.")


@app.command()
def analyze(
    org: str | None = typer.Option(None, help="GitHub organization name"),
    repo: str | None = typer.Option(None, help="Repository name"),
    period: str = typer.Option(
        "30d", callback=validate_period, help="Time period (e.g. 7d, 30d, 90d)"
    ),
    output: Path | None = typer.Option(None, help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full error tracebacks"),
):
    """
    Analyze GitHub repository development metrics.

    If --org and --repo are omitted, you will be prompted to select
    from your recently active repositories.
    """
    _validate_org_repo_pair(org, repo)

    typer.secho("Configuring GitHub Auth Token...", fg=typer.colors.BRIGHT_YELLOW, bold=True)
    token = get_github_token()

    if org is not None and repo is not None:
        selected = [f"{org}/{repo}"]
    else:
        repos = get_recent_repositories(token)
        selected = prompt_repo_selection(repos)

    typer.secho("Fetching development metrics...", fg=typer.colors.GREEN, bold=True)
    try:
        metrics = get_combined_metrics(token, selected, period)
    except GitHubError as e:
        typer.secho(f"Error fetching metrics: {e}", fg=typer.colors.RED, bold=True)
        if verbose:
            logger.exception("Full traceback:")
        raise typer.Exit(code=1) from e

    output_path = _resolve_output_path(output)
    _print_metrics(metrics, period, output_path)

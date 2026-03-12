import traceback
from pathlib import Path

import typer

from ..github import GitHubError, get_github_token
from ..metrics import get_combined_metrics, get_recent_repositories
from ..metrics.printer import CompositePrinter, get_default_output_path
from .prompts import prompt_repo_selection
from .validation import validate_period

app = typer.Typer()

DEFAULT_ORG: str | None = None
DEFAULT_REPO: str | None = None
DEFAULT_OUTPUT: Path | None = None


def _resolve_output_path(output: Path | None) -> Path:
    """Resolve output path from user input or return default."""
    return output if output else get_default_output_path()


def _print_metrics(metrics: dict, period: str, output_path: Path) -> None:
    """Print metrics to the specified output path."""
    CompositePrinter(output_path).print_combined_metrics(metrics, period)
    typer.secho(f"Results saved to {output_path}", fg=typer.colors.GREEN)


@app.command()
def analyze(
    org: str | None = typer.Option(DEFAULT_ORG, help="GitHub organization name"),
    repo: str | None = typer.Option(DEFAULT_REPO, help="Repository name"),
    period: str = typer.Option("30d", callback=validate_period, help="Time period"),
    output: Path | None = typer.Option(DEFAULT_OUTPUT, help="Output file path"),
):
    """
    Analyze GitHub repository development metrics.
    """

    if (org is None) != (repo is None):
        raise typer.BadParameter("Both --org and --repo must be provided, or neither") from None

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
        traceback.print_exc()
        raise typer.Exit(code=1) from e

    output_path = _resolve_output_path(output)
    _print_metrics(metrics, period, output_path)

import traceback

import typer
from rich.console import Console

from .validation import validate_period
from .prompts import prompt_repo_selection

from ..github import GitHubError, get_github_token
from ..metrics import get_combined_metrics, get_recent_repositories
from ..metrics.printer import CompositePrinter, get_default_output_path

app = typer.Typer()
console = Console()


@app.command()
def analyze(
    org: str | None = typer.Option(None, help="GitHub organization name"),
    repo: str | None = typer.Option(None, help="Repository name"),
    period: str = typer.Option("30d", callback=validate_period, help="Time period"),
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

    output_path = get_default_output_path()

    CompositePrinter(output_path).print_combined_metrics(metrics, period)

    typer.secho(f"Results saved to {output_path}", fg=typer.colors.GREEN)

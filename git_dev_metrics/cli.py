import traceback

import typer

from git_dev_metrics.type_definitions import GitHubError

from .auth.github_auth import get_github_token
from .client import GitHubClient
from .printer import print_metrics

app = typer.Typer()


def validate_period(period: str) -> str:
    if not period.endswith("d") or not period[:-1].isdigit():
        raise typer.BadParameter("Period must be like '7d', '30d', '90d'") from None
    return period


@app.command()
def analyze(
    org: str = typer.Option(..., help="GitHub organization name"),
    repo: str = typer.Option(..., help="Repository name"),
    period: str = typer.Option("30d", callback=validate_period, help="Time period"),
):
    """
    Analyze GitHub repository development metrics.
    """
    typer.secho("Configuring GitHub Auth Token...", fg=typer.colors.BRIGHT_YELLOW, bold=True)
    token = get_github_token()

    client = GitHubClient(token, org, repo)
    typer.secho("Fetching development metrics...", fg=typer.colors.GREEN, bold=True)

    try:
        metrics = client.get_development_metrics(period)
    except GitHubError as e:
        typer.secho(f"Error fetching metrics: {e}", fg=typer.colors.RED, bold=True)
        traceback.print_exc()
        raise typer.Exit(code=1) from e

    print_metrics(metrics, org, repo, period)


def main():
    app()


if __name__ == "__main__":
    app()

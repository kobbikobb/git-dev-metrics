import traceback

import questionary
from questionary import Style
import typer
from rich.console import Console

from .github import GitHubError, get_github_token
from .metrics import get_pull_request_metrics, get_recent_repositories, print_metrics

app = typer.Typer()
console = Console()


def validate_period(period: str) -> str:
    if not period.endswith("d") or not period[:-1].isdigit():
        raise typer.BadParameter("Period must be like '7d', '30d', '90d'") from None
    return period


def prompt_repo_selection(repos: dict[str, str]) -> list[str]:
    choices = [
        questionary.Choice(
            title=f"{name} ({visibility})",
            value=name,
            checked=True,  # all selected by default
        )
        for name, visibility in repos.items()
    ]

    custom_style = Style(
        [
            ("highlighted", "fg:#00b4d8 bold"),  # cursor row
            ("selected", "fg:#90e0ef"),  # checked items
        ]
    )

    selected = questionary.checkbox(
        "Select repositories to include:", choices=choices, style=custom_style
    ).ask()

    return selected or list(repos.keys())  # fallback if user cancels


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

    for full_name in selected:
        repo_org, repo_name = full_name.split("/", 1)
        try:
            metrics = get_pull_request_metrics(token, repo_org, repo_name, period)
        except GitHubError as e:
            typer.secho(
                f"Error fetching metrics for {full_name}: {e}", fg=typer.colors.RED, bold=True
            )
            traceback.print_exc()
            raise typer.Exit(code=1) from e

        print_metrics(metrics, repo_org, repo_name, period)


def main():
    app()


if __name__ == "__main__":
    app()

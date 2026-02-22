import traceback

import typer
from rich.console import Console
from rich.table import Table

from .github import GitHubError, get_github_token
from .metrics import get_all_repositories, get_pull_request_metrics, print_metrics

app = typer.Typer()
console = Console()


def validate_period(period: str) -> str:
    if not period.endswith("d") or not period[:-1].isdigit():
        raise typer.BadParameter("Period must be like '7d', '30d', '90d'") from None
    return period


def prompt_repo_selection(repos: dict[str, str]) -> list[str]:
    repo_list = list(repos.keys())

    table = Table(title="Available Repositories")
    table.add_column("#", style="cyan")
    table.add_column("Repository", style="green")
    table.add_column("Visibility", style="yellow")

    for i, name in enumerate(repo_list, 1):
        table.add_row(str(i), name, repos[name])

    console.print(table)
    console.print("\n[bold]All repos selected by default.[/bold]")
    console.print("Enter numbers to deselect (e.g., 1,3,5) or press Enter to continue with all: ")

    deselect_input = input().strip()
    if deselect_input:
        try:
            deselect_nums = set(int(x.strip()) for x in deselect_input.split(",") if x.strip())
            selected = [name for i, name in enumerate(repo_list, 1) if i not in deselect_nums]
        except ValueError:
            console.print("[red]Invalid input. Using all repos.[/red]")
            selected = repo_list
    else:
        selected = repo_list

    return selected


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

    all_repos = get_all_repositories(token)

    if org is not None and repo is not None:
        selected = [f"{org}/{repo}"]
    else:
        selected = prompt_repo_selection(all_repos)

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

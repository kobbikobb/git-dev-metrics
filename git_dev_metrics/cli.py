import typer

from .auth import get_github_token
from .client import GitHubClient

app = typer.Typer()


@app.command()
def analyze(org: str, repo: str, period: str = "30d"):
    """
    Analyze GitHub repository development metrics.

    Args:
        org (str): The GitHub organization name.
        repo (str): The GitHub repository name.
        period (str): The time period for analysis (default is "month").
    """
    token = get_github_token()
    client = GitHubClient(token, org, repo)

    metrics = client.get_development_metrics(period)

    typer.echo(f"Development Metrics for {org}/{repo} over the past {period}:")

    for key, value in metrics.items():
        typer.echo(f"{key}: {value}")


if __name__ == "__main__":
    app()

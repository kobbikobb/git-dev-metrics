import typer


def validate_period(period: str) -> str:
    if not period.endswith("d") or not period[:-1].isdigit():
        raise typer.BadParameter("Period must be like '7d', '30d', '90d'") from None
    return period


def validate_org_repo_pair(org: str | None, repo: str | None) -> None:
    """Ensure org and repo are either both provided or both omitted."""
    if (org is None) != (repo is None):
        raise typer.BadParameter("Both --org and --repo must be provided together, or neither.")

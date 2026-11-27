from collections.abc import Callable
from pathlib import Path

import typer

from ...cache import list_synced_months
from ...github.auth_cache import load_token


def load_report_prs(
    months: list[tuple[int, int]],
    db_path: Path | None,
    fetch: Callable[[str, str, str, int, int], list[dict]],
) -> list[dict]:
    token = load_token()
    if not token:
        typer.secho("No GitHub token found. Run login first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    wanted = set(months)
    prs: dict[tuple[str, str, int], dict] = {}
    for org, repo, year, month in list_synced_months(db_path=db_path):
        if (year, month) in wanted:
            for pr in fetch(token, org, repo, year, month):
                prs.setdefault((org, repo, pr["number"]), pr)

    if not prs:
        typer.secho("No PRs found for selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    return list(prs.values())

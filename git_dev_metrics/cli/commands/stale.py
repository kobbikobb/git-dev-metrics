from datetime import datetime
from pathlib import Path

import typer

from ...cache import list_synced_months
from ...github import fetch_open_prs, get_github_token
from ...metrics._rows import StalePr
from ...metrics.calculator import get_stale_prs
from ...metrics.printer.stale import FileStaleHtmlPrinter
from .._browser import open_in_browser


def _default_output() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return Path(f"./metrics_results/stale_{today}.html")


def stale(
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    repos = sorted({(org, repo) for org, repo, *_ in list_synced_months(db_path=db)})
    if not repos:
        typer.secho("No repos in cache — run pull first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    token = get_github_token()
    all_stale: list[StalePr] = []
    for org, repo in repos:
        opens = fetch_open_prs(token, org, repo, quiet=True)
        all_stale.extend(get_stale_prs(opens, f"{org}/{repo}"))
    all_stale.sort(key=lambda x: x.age_hours, reverse=True)

    out = (output or _default_output()).with_suffix(".html")
    FileStaleHtmlPrinter(out).render(all_stale)
    typer.echo(f"Stale written to {out}.")
    open_in_browser(out)

from datetime import datetime
from pathlib import Path

import typer

from ...cache import get_targets, list_synced_months
from ...github import (
    GitHubError,
    GitHubNotFoundError,
    fetch_open_pr_build_state,
    fetch_open_pr_security,
    fetch_open_prs,
    get_github_token,
    is_repo_archived,
)
from ...metrics._stale_pr import StalePr, get_stale_prs
from ...metrics.printer.stale import FileStaleHtmlPrinter
from ...models import OpenPullRequest, SecurityInfo
from .._browser import open_in_browser
from .._options import DB_OPTION


def _default_output() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return Path(f"./metrics_results/stale_{today}.html")


def _apply_build_state(
    token: str,
    org: str,
    repo: str,
    opens: list[OpenPullRequest],
    flags: dict[str, bool],
) -> None:
    """Backfill build_state from Actions workflow runs."""
    try:
        build = fetch_open_pr_build_state(
            token, org, repo, {pr["number"]: pr.get("head_sha") for pr in opens}
        )
    except GitHubError as e:
        if not flags["build_warned"]:
            typer.secho(
                f"Build status unavailable for {org}/{repo}: {e}",
                fg=typer.colors.YELLOW,
                err=True,
            )
            flags["build_warned"] = True
        return
    for pr in opens:
        if pr["number"] in build:
            pr["build_state"] = build[pr["number"]]


def _repo_stale(
    token: str,
    org: str,
    repo: str,
    threshold_hours: float,
    flags: dict[str, bool],
) -> list[StalePr] | None:
    """Fetch stale PRs for one repo, degrading gracefully; None means skip."""
    try:
        if is_repo_archived(token, org, repo):
            typer.secho(f"Skipping {org}/{repo} — archived", fg=typer.colors.YELLOW, err=True)
            return None
    except GitHubError as e:
        typer.secho(f"Skipping {org}/{repo} — {e}", fg=typer.colors.YELLOW, err=True)
        return None

    try:
        opens = fetch_open_prs(token, org, repo, quiet=True)
    except GitHubNotFoundError:
        typer.secho(
            f"Skipping {org}/{repo} — not found on GitHub",
            fg=typer.colors.YELLOW,
            err=True,
        )
        return None
    except GitHubError as e:
        typer.secho(f"Skipping {org}/{repo} — {e}", fg=typer.colors.YELLOW, err=True)
        return None

    _apply_build_state(token, org, repo, opens, flags)

    security: dict[int, SecurityInfo] = {}
    try:
        security = fetch_open_pr_security(token, org, repo)
    except GitHubNotFoundError as e:
        if not flags["security_warned"]:
            typer.secho(f"Security alerts unavailable: {e}", fg=typer.colors.YELLOW, err=True)
            flags["security_warned"] = True
    except GitHubError as e:
        if not flags["security_warned"]:
            typer.secho(
                f"Security alerts skipped for {org}/{repo}: {e}",
                fg=typer.colors.YELLOW,
                err=True,
            )
            flags["security_warned"] = True
    return get_stale_prs(opens, f"{org}/{repo}", threshold_hours=threshold_hours, security=security)


def stale(
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = DB_OPTION,
) -> None:
    """Find stale open PRs across all cached repos."""
    repos = sorted({(org, repo) for org, repo, *_ in list_synced_months(db_path=db)})
    if not repos:
        typer.secho("No repos in cache — run pull first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    targets = get_targets(db_path=db)
    threshold_days = targets.get("stale_threshold_days", 7)
    threshold_hours = threshold_days * 24

    token = get_github_token()
    all_stale: list[StalePr] = []
    flags = {"build_warned": False, "security_warned": False}
    for org, repo in repos:
        repo_stale = _repo_stale(token, org, repo, threshold_hours, flags)
        if repo_stale:
            all_stale.extend(repo_stale)
    all_stale.sort(key=lambda x: x.age_hours, reverse=True)

    out = (output or _default_output()).with_suffix(".html")
    FileStaleHtmlPrinter(out).render(all_stale, targets=targets)
    typer.echo(f"Stale written to {out.resolve().as_uri()}.")
    open_in_browser(out)

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import questionary
import typer
from questionary import Style

from ...cache import is_sealed
from ...github import (
    fetch_org_repositories,
    fetch_repositories,
    get_github_token,
    load_last_org,
    save_last_org,
)
from ...github.queries import fetch_repo_metrics
from ...models import PullRequest, Repository
from ...utils.date_utils import TimePeriod, month_range, parse_year_month
from ..runners.pull_runner import fetch_and_seal_month
from .prompts import prompt_org_name, prompt_repo_selection

_STYLE = Style([("highlighted", "fg:#00b4d8 bold"), ("selected", "fg:#90e0ef")])
_MONTHS_LOOKBACK = 12

MonthChoice = tuple[str, str]


def _candidate_months(now: datetime) -> list[MonthChoice]:
    """Past `_MONTHS_LOOKBACK` complete calendar months, newest first."""
    out: list[MonthChoice] = []
    year, month = now.year, now.month
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    for _ in range(_MONTHS_LOOKBACK):
        out.append((datetime(year, month, 1).strftime("%B %Y"), f"{year:04d}-{month:02d}"))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return out


def _prompt_month_pick(choices: list[MonthChoice]) -> str | None:
    items = [questionary.Choice(title=label, value=value) for label, value in choices]
    return questionary.select("Select month to pull:", choices=items, style=_STYLE).ask()


def _default_fetch_repos(token: str, org: str | None) -> list[Repository]:
    return fetch_org_repositories(token, org) if org else fetch_repositories(token)


def _filter_active(repos: list[Repository], since: datetime) -> list[Repository]:
    return [r for r in repos if r.get("last_pushed") and r["last_pushed"] >= since]  # type: ignore[reportOperatorIssue]


def pull_wizard(
    db_path: Path | None = None,
    *,
    ask_org: Callable[[str | None], str | None] = prompt_org_name,
    ask_month: Callable[[list[MonthChoice]], str | None] = _prompt_month_pick,
    ask_repos: Callable[[dict[str, str]], list[str]] = prompt_repo_selection,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    fetch: Callable[..., list[PullRequest]] = fetch_repo_metrics,
    fetch_repos: Callable[[str, str | None], list[Repository]] = _default_fetch_repos,
    get_token: Callable[[], str] = get_github_token,
) -> None:
    """Interactive flow: pick org, month, repos, then pull + seal that month per repo."""
    org = ask_org(load_last_org())
    if not org:
        typer.secho("Org is required.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    save_last_org(org)

    picked = ask_month(_candidate_months(clock()))
    if not picked:
        raise typer.Exit(code=1)
    try:
        year, month_num = parse_year_month(picked)
    except ValueError:
        typer.secho(f"Invalid month '{picked}'; expected YYYY-MM.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None
    period = month_range(year, month_num)
    if period.until > clock():
        typer.secho(f"Month {picked} is incomplete; cannot seal.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    token = get_token()
    active = _filter_active(fetch_repos(token, org), period.since)
    if not active:
        typer.secho(f"No active repos for {org} in {picked}.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    options = {r["full_name"]: "Private" if r["private"] else "Public" for r in active}
    selected = ask_repos(options)
    if not selected:
        raise typer.Exit(code=1)

    _pull_each(selected, year, month_num, period, token, fetch, db_path)


def _pull_each(
    selected: list[str],
    year: int,
    month_num: int,
    period: TimePeriod,
    token: str,
    fetch: Callable[..., list[PullRequest]],
    db_path: Path | None,
) -> None:
    pulled = 0
    skipped = 0
    for full_name in selected:
        org, repo = full_name.split("/", 1)
        if is_sealed(org, repo, year, month_num, db_path=db_path):
            typer.echo(f"Skipped {full_name}: already sealed.")
            skipped += 1
            continue
        n = fetch_and_seal_month(org, repo, year, month_num, period, token, db_path, fetch=fetch)
        typer.echo(f"Pulled {n} PRs for {full_name}.")
        pulled += 1
    typer.echo(f"Done. Pulled {pulled}, skipped {skipped}.")

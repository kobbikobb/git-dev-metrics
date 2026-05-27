from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import questionary
import typer

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
from ...utils.date_utils import TimePeriod, month_range
from .._month_arg import parse_month_arg
from ..runners.pull_runner import fetch_and_seal_month
from ._wizard import _STYLE
from .prompts import prompt_org_name, prompt_repo_selection

_MONTHS_LOOKBACK = 12

MonthChoice = tuple[str, str]


def _candidate_months(now: datetime) -> list[MonthChoice]:
    """`_MONTHS_LOOKBACK` months including current, newest first."""
    out: list[MonthChoice] = []
    year, month = now.year, now.month
    for _ in range(_MONTHS_LOOKBACK):
        label = datetime(year, month, 1).strftime("%B %Y")
        if year == now.year and month == now.month:
            label += " (current)"
        out.append((label, f"{year:04d}-{month:02d}"))
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
    return [r for r in repos if (pushed := r.get("last_pushed")) is not None and pushed >= since]


def _select_org_month(
    ask_org: Callable[[str | None], str | None],
    ask_month: Callable[[list[MonthChoice]], str | None],
    clock: Callable[[], datetime],
) -> tuple[str, str, int, int, TimePeriod]:
    org = ask_org(load_last_org())
    if not org:
        typer.secho("Org is required.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    save_last_org(org)

    picked = ask_month(_candidate_months(clock()))
    if not picked:
        raise typer.Exit(code=1)
    year, month_num = parse_month_arg(picked)
    period = month_range(year, month_num)

    return org, picked, year, month_num, period


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
    org, picked, year, month_num, period = _select_org_month(ask_org, ask_month, clock)

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
    partial = period.until > datetime.now(UTC)
    for full_name in selected:
        org, repo = full_name.split("/", 1)
        if is_sealed(org, repo, year, month_num, db_path=db_path):
            typer.echo(f"Skipped {full_name}: already sealed.")
            skipped += 1
            continue
        n = fetch_and_seal_month(
            org,
            repo,
            year,
            month_num,
            period,
            token,
            db_path,
            fetch=fetch,
            partial=partial,
        )
        tag = " (partial)" if partial else ""
        typer.echo(f"Pulled {n} PRs for {full_name}.{tag}")
        pulled += 1
    typer.echo(f"Done. Pulled {pulled}, skipped {skipped}.")

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import questionary
import typer
from questionary import Style

from ..cache import list_synced_months
from .trend_runner import perform_trend

RepoMonths = dict[tuple[str, str], list[tuple[int, int]]]
RepoKey = tuple[str, str]
YearMonth = tuple[int, int]

_STYLE = Style([("highlighted", "fg:#00b4d8 bold"), ("selected", "fg:#90e0ef")])


def _group_by_repo(synced: list[tuple[str, str, int, int]]) -> RepoMonths:
    out: RepoMonths = {}
    for org, repo, year, month in synced:
        out.setdefault((org, repo), []).append((year, month))
    for key in out:
        out[key].sort()
    return out


def _prompt_repo_pick(repos: list[RepoKey]) -> RepoKey | None:
    items = [questionary.Choice(title=f"{org}/{repo}", value=(org, repo)) for org, repo in repos]
    return questionary.select("Select repository:", choices=items, style=_STYLE).ask()


def _month_choices(months: list[YearMonth]) -> list[questionary.Choice]:
    return [
        questionary.Choice(title=datetime(y, m, 1).strftime("%B %Y"), value=(y, m))
        for y, m in months
    ]


def _prompt_from(months: list[YearMonth]) -> YearMonth | None:
    return questionary.select(
        "From month:", choices=_month_choices(list(reversed(months))), style=_STYLE
    ).ask()


def _prompt_to(months: list[YearMonth]) -> YearMonth | None:
    return questionary.select(
        "To month:", choices=_month_choices(list(reversed(months))), style=_STYLE
    ).ask()


def trend_wizard(
    db_path: Path | None = None,
    *,
    ask_repo_pick: Callable[[list[RepoKey]], RepoKey | None] = _prompt_repo_pick,
    ask_from: Callable[[list[YearMonth]], YearMonth | None] = _prompt_from,
    ask_to: Callable[[list[YearMonth]], YearMonth | None] = _prompt_to,
) -> None:
    """Interactive flow: pick repo + from/to month range from synced cache, render trend HTML."""
    synced = list_synced_months(db_path=db_path)
    if not synced:
        typer.secho("No synced months — run gdm pull first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    grouped = _group_by_repo(synced)
    repo = ask_repo_pick(sorted(grouped.keys()))
    if repo is None:
        raise typer.Exit(code=1)

    months = grouped[repo]
    from_ym = ask_from(months)
    if from_ym is None:
        raise typer.Exit(code=1)
    to_candidates = [ym for ym in months if ym >= from_ym]
    to_ym = ask_to(to_candidates)
    if to_ym is None:
        raise typer.Exit(code=1)

    perform_trend(repo[0], repo[1], from_ym, to_ym, output=None, db_path=db_path)

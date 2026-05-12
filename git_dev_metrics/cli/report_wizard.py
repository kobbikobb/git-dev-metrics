from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import questionary
import typer
from questionary import Style

from ..cache import list_synced_months, load_all_repos_for_range
from ..metrics.analyzer import build_combined_metrics_for_repos
from ..utils.date_utils import range_period
from .report_runner import render_combined

_DATE_FMT = "%Y-%m-%d"
_STYLE = Style([("highlighted", "fg:#00b4d8 bold"), ("selected", "fg:#90e0ef")])

YearMonth = tuple[int, int]


def _prompt_months(months: list[YearMonth]) -> list[YearMonth]:
    """Multi-select over sealed months, newest first, all checked by default."""
    items = [
        questionary.Choice(
            title=datetime(y, m, 1).strftime("%B %Y"),
            value=(y, m),
            checked=True,
        )
        for y, m in months
    ]
    return (
        questionary.checkbox("Select months to include:", choices=items, style=_STYLE).ask() or []
    )


def _slug(ym: YearMonth) -> str:
    return f"{ym[0]:04d}-{ym[1]:02d}"


def report_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Interactive flow: pick months from synced cache, render aggregated dashboard."""
    synced = list_synced_months(db_path=db_path)
    if not synced:
        typer.secho("No synced months — run gdm pull first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    months_avail = sorted({(y, m) for _, _, y, m in synced}, reverse=True)
    picked = ask_months(months_avail)
    if not picked:
        raise typer.Exit(code=1)

    selected = sorted(picked)
    repo_prs = load_all_repos_for_range(selected, db_path=db_path)
    if not repo_prs:
        typer.secho("No PRs in selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    period = range_period(selected[0], selected[-1])
    metrics = build_combined_metrics_for_repos(repo_prs, period)
    period_slug = f"{_slug(selected[0])}-to-{_slug(selected[-1])}"
    date_range = f"{period.since.strftime(_DATE_FMT)} to {period.until.strftime(_DATE_FMT)}"
    render_combined(metrics, period_slug, date_range, output=None)

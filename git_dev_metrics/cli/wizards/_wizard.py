from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import questionary
import typer
from questionary import Style

from ...cache import list_synced_months
from ...metrics.loader import load_snapshot_for_months
from ...metrics.snapshot import MetricsSnapshot
from ..utils._date_formatter import format_date_range

YearMonth = tuple[int, int]

_STYLE = Style([("highlighted", "fg:#00b4d8 bold"), ("selected", "fg:#90e0ef")])


def _prompt_months(months: list[YearMonth]) -> list[YearMonth]:
    items = [
        questionary.Choice(title=datetime(y, m, 1).strftime("%B %Y"), value=(y, m), checked=True)
        for y, m in months
    ]
    return (
        questionary.checkbox("Select months to include:", choices=items, style=_STYLE).ask() or []
    )


def pick_months(
    db_path: Path | None,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> list[YearMonth]:
    synced = list_synced_months(db_path=db_path)
    if not synced:
        typer.secho("No synced months — run pull first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    months_avail = sorted({(y, m) for _, _, y, m in synced}, reverse=True)
    picked = ask_months(months_avail)
    if not picked:
        raise typer.Exit(code=1)
    return sorted(picked)


def run_wizard(
    db_path: Path | None,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]],
    output_fn: Callable[[MetricsSnapshot, str, str], None],
) -> None:
    selected = pick_months(db_path, ask_months)
    snapshot = load_snapshot_for_months(selected, db_path)
    if snapshot is None:
        typer.secho("No PRs in selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    first, last = selected[0], selected[-1]
    period_slug = f"{first[0]:04d}-{first[1]:02d}-to-{last[0]:04d}-{last[1]:02d}"
    output_fn(snapshot, period_slug, format_date_range(snapshot.period))

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import questionary
import typer
from questionary import Style

from ..cache import list_synced_months

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

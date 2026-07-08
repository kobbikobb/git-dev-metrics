from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import questionary
import typer

from ...cache import list_synced_months
from ..runners.team_velocity_runner import perform_team_velocity
from ._wizard import _STYLE, YearMonth


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


def team_velocity_wizard(
    db_path: Path | None = None,
    *,
    ask_from: Callable[[list[YearMonth]], YearMonth | None] = _prompt_from,
    ask_to: Callable[[list[YearMonth]], YearMonth | None] = _prompt_to,
) -> None:
    """Pick from/to months across the union of synced months; render team velocity HTML."""
    synced = list_synced_months(db_path=db_path)
    if not synced:
        typer.secho("No synced months — run pull first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    months = sorted({(y, m) for _, _, y, m in synced})
    from_ym = ask_from(months)
    if from_ym is None:
        raise typer.Exit(code=1)
    to_candidates = [ym for ym in months if ym >= from_ym]
    to_ym = ask_to(to_candidates)
    if to_ym is None:
        raise typer.Exit(code=1)

    perform_team_velocity(from_ym, to_ym, output=None, db_path=db_path)

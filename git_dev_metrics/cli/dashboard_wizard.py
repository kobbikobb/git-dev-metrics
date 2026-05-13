from collections.abc import Callable
from pathlib import Path

import typer

from ._metrics import metrics_for_months
from ._wizard import _prompt_months, pick_months
from .dashboard_runner import write_and_open_dashboard

YearMonth = tuple[int, int]


def dashboard_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Pick months from cache, render HTML dashboard, open in browser."""
    selected = pick_months(db_path, ask_months)
    result = metrics_for_months(selected, db_path)
    if result is None:
        typer.secho("No PRs in selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    metrics, period_slug, date_range = result
    write_and_open_dashboard(metrics, period_slug, date_range, output=None)

from collections.abc import Callable
from pathlib import Path

import typer

from ..metrics.printer import ConsolePrinter
from ._metrics import metrics_for_months
from ._wizard import _prompt_months, pick_months

YearMonth = tuple[int, int]


def summary_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Pick months from cache, print aggregated summary to console."""
    selected = pick_months(db_path, ask_months)
    result = metrics_for_months(selected, db_path)
    if result is None:
        typer.secho("No PRs in selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    metrics, period_slug, date_range = result
    ConsolePrinter().print_combined_metrics(metrics, period_slug, date_range)

from collections.abc import Callable
from pathlib import Path

import typer

from ..metrics.loader import load_snapshot_for_months
from ..metrics.printer import ConsolePrinter
from ._wizard import _prompt_months, pick_months

YearMonth = tuple[int, int]


def summary_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Pick months from cache, print aggregated summary to console."""
    selected = pick_months(db_path, ask_months)
    snapshot = load_snapshot_for_months(selected, db_path)
    if snapshot is None:
        typer.secho("No PRs in selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    first, last = selected[0], selected[-1]
    period_slug = f"{first[0]:04d}-{first[1]:02d}-to-{last[0]:04d}-{last[1]:02d}"
    since = snapshot.period.since.strftime("%Y-%m-%d")
    until = snapshot.period.until.strftime("%Y-%m-%d")
    ConsolePrinter().print_combined_metrics(snapshot, period_slug, f"{since} to {until}")

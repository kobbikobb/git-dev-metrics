from collections.abc import Callable
from pathlib import Path

from ...metrics.printer import ConsolePrinter
from ._wizard import YearMonth, _prompt_months, run_wizard


def summary_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Pick months from cache, print aggregated summary to console."""
    run_wizard(
        db_path,
        ask_months,
        lambda s, slug, dr: ConsolePrinter().print_combined_metrics(s, slug, dr),
    )

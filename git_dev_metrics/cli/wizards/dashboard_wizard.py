from collections.abc import Callable
from pathlib import Path

from ...cache import get_nicknames
from ..runners.dashboard_runner import write_and_open_dashboard
from ._wizard import YearMonth, _prompt_months, run_wizard


def dashboard_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Pick months from cache, render HTML dashboard, open in browser."""
    nicknames = get_nicknames(db_path=db_path)
    run_wizard(
        db_path,
        ask_months,
        lambda s, slug, dr: write_and_open_dashboard(s, slug, dr, output=None, nicknames=nicknames),
    )

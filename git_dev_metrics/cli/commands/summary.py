from pathlib import Path

import typer

from ...cache import get_nicknames, get_targets
from ...metrics.printer import ConsolePrinter
from .._options import DB_OPTION
from ..utils._date_formatter import format_date_range
from ..wizards.summary_wizard import summary_wizard
from ._resolve_range import resolve_range


def summary(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    db: Path | None = DB_OPTION,
) -> None:
    """Print the dashboard summary to the console."""
    snapshot = resolve_range(from_, to, db, summary_wizard)
    nicknames = get_nicknames(db_path=db)
    targets = get_targets(db_path=db)
    ConsolePrinter().print_combined_metrics(
        snapshot, format_date_range(snapshot.period), nicknames=nicknames, targets=targets
    )

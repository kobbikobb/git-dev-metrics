from pathlib import Path

import typer

from ...metrics.printer import ConsolePrinter
from ..utils._date_formatter import format_date_range
from ..wizards.summary_wizard import summary_wizard
from ._resolve_range import resolve_range


def summary(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Print the dashboard summary to the console."""
    snapshot = resolve_range(from_, to, db, summary_wizard)
    ConsolePrinter().print_combined_metrics(
        snapshot, f"{from_}-to-{to}", format_date_range(snapshot.period)
    )

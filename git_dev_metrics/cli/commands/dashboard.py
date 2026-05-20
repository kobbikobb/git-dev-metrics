from pathlib import Path

import typer

from .._options import DB_OPTION
from ..runners.dashboard_runner import write_and_open_dashboard
from ..utils._date_formatter import format_date_range
from ..wizards.dashboard_wizard import dashboard_wizard
from ._resolve_range import resolve_range


def dashboard(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = DB_OPTION,
) -> None:
    """Render the in-depth HTML dashboard and open it in the browser."""
    snapshot = resolve_range(from_, to, db, dashboard_wizard)
    write_and_open_dashboard(
        snapshot, f"{from_}-to-{to}", format_date_range(snapshot.period), output
    )

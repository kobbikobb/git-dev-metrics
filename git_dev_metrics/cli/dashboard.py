from pathlib import Path

import typer

from ._metrics import metrics_for_range
from .dashboard_runner import write_and_open_dashboard
from .dashboard_wizard import dashboard_wizard


def dashboard(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Render the in-depth HTML dashboard and open it in the browser."""
    if from_ is None and to is None:
        dashboard_wizard(db_path=db)
        return

    if from_ is None or to is None:
        typer.secho(
            "Provide both --from and --to, or neither (for the wizard).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    metrics, period_slug, date_range = metrics_for_range(from_, to, db)
    write_and_open_dashboard(metrics, period_slug, date_range, output)

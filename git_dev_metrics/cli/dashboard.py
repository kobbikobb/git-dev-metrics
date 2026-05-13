from pathlib import Path

import typer

from ..metrics.loader import InvalidRangeError, load_snapshot_for_range
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

    try:
        snapshot = load_snapshot_for_range(from_, to, db)
    except InvalidRangeError:
        typer.secho("--to must be >= --from.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None
    if snapshot is None:
        typer.secho(
            f"No synced data for {from_} to {to}. Run pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    period_slug = f"{from_}-to-{to}"
    since = snapshot.period.since.strftime("%Y-%m-%d")
    until = snapshot.period.until.strftime("%Y-%m-%d")
    write_and_open_dashboard(snapshot, period_slug, f"{since} to {until}", output)

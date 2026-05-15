from pathlib import Path

import typer

from ...metrics.loader import InvalidRangeError, load_snapshot_for_range
from ...metrics.printer import ConsolePrinter
from ..wizards.summary_wizard import summary_wizard


def summary(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Print the dashboard summary to the console."""
    if from_ is None and to is None:
        summary_wizard(db_path=db)
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
    ConsolePrinter().print_combined_metrics(snapshot, period_slug, f"{since} to {until}")

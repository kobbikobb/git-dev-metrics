from pathlib import Path

import typer

from ..metrics.printer import ConsolePrinter
from ._metrics import metrics_for_range
from .summary_wizard import summary_wizard


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

    metrics, period_slug, date_range = metrics_for_range(from_, to, db)
    ConsolePrinter().print_combined_metrics(metrics, period_slug, date_range)

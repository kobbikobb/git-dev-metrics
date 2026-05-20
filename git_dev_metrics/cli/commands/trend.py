from pathlib import Path

import typer

from .._month_arg import parse_month_arg
from .._options import DB_OPTION
from ..runners.trend_runner import perform_trend
from ..wizards.trend_wizard import trend_wizard


def trend(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = DB_OPTION,
) -> None:
    """Render a multi-month trend HTML aggregated across all cached repos."""
    if from_ is None and to is None:
        trend_wizard(db_path=db)
        return

    if from_ is None or to is None:
        typer.secho(
            "Provide both --from and --to, or neither (for the wizard).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    from_ym = parse_month_arg(from_, "--from")
    to_ym = parse_month_arg(to, "--to")
    perform_trend(from_ym, to_ym, output=output, db_path=db)

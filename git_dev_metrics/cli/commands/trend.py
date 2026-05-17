from pathlib import Path

import typer

from ...utils.date_utils import parse_year_month
from ..runners.trend_runner import perform_trend
from ..wizards.trend_wizard import trend_wizard


def trend(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
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

    try:
        from_ym = parse_year_month(from_)
    except ValueError:
        typer.secho(f"Invalid --from '{from_}'; expected YYYY-MM.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None
    try:
        to_ym = parse_year_month(to)
    except ValueError:
        typer.secho(f"Invalid --to '{to}'; expected YYYY-MM.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None
    perform_trend(from_ym, to_ym, output=output, db_path=db)

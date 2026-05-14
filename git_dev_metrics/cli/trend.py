from pathlib import Path

import typer

from ..utils.date_utils import parse_year_month
from .trend_runner import perform_trend
from .trend_wizard import trend_wizard


def _parse_month_arg(value: str, flag: str = "--month") -> tuple[int, int]:
    try:
        return parse_year_month(value)
    except ValueError as e:
        typer.secho(f"Invalid {flag} '{value}'; expected YYYY-MM.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


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

    from_ym = _parse_month_arg(from_, "--from")
    to_ym = _parse_month_arg(to, "--to")
    perform_trend(from_ym, to_ym, output=output, db_path=db)

from pathlib import Path

import typer

from ...utils.date_utils import month_iter
from .._month_arg import parse_month_arg
from ..runners.lang_runner import perform_lang_report
from ..wizards.lang_wizard import lang_wizard


def lang_report(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Render a language breakdown report for selected months."""
    if from_ is None and to is None:
        lang_wizard(db_path=db)
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
    if to_ym < from_ym:
        typer.secho("--to must be >= --from.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    months = month_iter(from_ym, to_ym)
    perform_lang_report(months, output=output, db_path=db)

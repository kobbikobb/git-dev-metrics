from pathlib import Path

import typer

from ...utils.date_utils import last_n_months
from .._month_arg import parse_month_arg
from .._options import DB_OPTION
from ..runners.team_velocity_runner import perform_team_velocity
from ..wizards.team_velocity_wizard import team_velocity_wizard


def team_velocity(
    mode: str | None = typer.Argument(None, help="'current' for last 12 months"),
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = DB_OPTION,
) -> None:
    """Render a team velocity chart: merged PRs per developer over time."""
    if mode == "current":
        from_ym, to_ym = last_n_months(12, include_current=True)
        perform_team_velocity(from_ym, to_ym, output=output, db_path=db)
        return

    if from_ is None and to is None:
        team_velocity_wizard(db_path=db)
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
    perform_team_velocity(from_ym, to_ym, output=output, db_path=db)

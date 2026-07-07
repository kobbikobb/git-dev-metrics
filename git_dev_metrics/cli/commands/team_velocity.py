from pathlib import Path

import typer

from ...utils.date_utils import last_n_months
from .._options import DB_OPTION
from ..runners.team_velocity_runner import perform_team_velocity


def team_velocity(
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = DB_OPTION,
) -> None:
    """Render a team velocity chart: merged PRs vs active developers over time."""
    from_ym, to_ym = last_n_months(12, include_current=True)
    perform_team_velocity(from_ym, to_ym, output=output, db_path=db)

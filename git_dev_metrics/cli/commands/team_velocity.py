from pathlib import Path

import questionary
import typer

from ...cache import list_synced_months
from ...utils.date_utils import last_n_months, month_iter
from .._options import DB_OPTION
from ..runners.team_velocity_runner import perform_team_velocity
from ..wizards._wizard import _STYLE


def team_velocity(
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = DB_OPTION,
) -> None:
    """Render a team velocity chart: merged PRs vs active developers over time."""
    from_ym, to_ym = last_n_months(12, include_current=True)

    wanted = set(month_iter(from_ym, to_ym))
    all_repos = sorted(
        {f"{org}/{repo}" for org, repo, y, m in list_synced_months(db_path=db) if (y, m) in wanted}
    )
    if not all_repos:
        typer.secho(
            "No synced data for selected range. Run pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    selected = questionary.checkbox(
        "Select repositories:",
        choices=[questionary.Choice(title=repo, value=repo, checked=False) for repo in all_repos],
        style=_STYLE,
    ).ask()
    if selected is None:
        raise typer.Exit(code=1)

    perform_team_velocity(from_ym, to_ym, repos=selected, output=output, db_path=db)

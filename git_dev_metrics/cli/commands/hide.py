from pathlib import Path

import typer

from ...cache import get_all_dev_logins, get_hidden_logins, get_nicknames, update_hidden_logins
from .._options import DB_OPTION


def hide(db: Path | None = DB_OPTION) -> None:
    """Hide or show developers in individual report results."""
    hidden = get_hidden_logins(db_path=db)
    logins = {login.lower() for login in get_all_dev_logins(db_path=db)} | hidden
    if not logins:
        typer.secho("No cached data found. Pull some months first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    nicknames = {login.lower(): name for login, name in get_nicknames(db_path=db).items()}
    typer.echo("Hidden developers still count toward team metrics. Press Enter to keep a setting.")
    changes: dict[str, bool] = {}
    for login in sorted(logins):
        label = f"{login} ({nicknames[login]})" if login in nicknames else login
        was_hidden = login in hidden
        state = "hidden" if was_hidden else "visible"
        hide_login = typer.confirm(f"Hide {label} (currently {state})?", default=was_hidden)
        if hide_login != was_hidden:
            changes[login] = hide_login

    update_hidden_logins(changes, db_path=db)
    typer.echo(f"Saved visibility changes for {len(changes)} developers.")

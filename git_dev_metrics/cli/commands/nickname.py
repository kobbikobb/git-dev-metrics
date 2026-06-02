from pathlib import Path

import typer

from ...cache import delete_nickname, get_all_dev_logins, get_nicknames, set_nickname


def _print_nicknames(logins: list[str], current: dict[str, str]) -> None:
    typer.echo("")
    typer.echo("Current nicknames:")
    for login in logins:
        nick = current.get(login, login)
        marker = "" if nick == login else f" → {nick}"
        typer.echo(f"  {login}{marker}")


def nickname(
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Set display nicknames for developers in reports."""
    logins = sorted(get_all_dev_logins(db_path=db))
    if not logins:
        typer.secho(
            "No cached data found. Pull some months first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    current = get_nicknames(db_path=db)
    typer.echo(f"Found {len(logins)} developers.")
    typer.echo("Enter a display name for each developer (blank keeps current, 'x' clears):")

    for login in logins:
        existing = current.get(login, "")
        hint = f" [{existing}]" if existing else ""
        val = typer.prompt(f"  {login}{hint}", default="", show_default=False, prompt_suffix="> ")

        if val == "x":
            if existing:
                delete_nickname(login, db_path=db)
                del current[login]
        elif val and val != existing:
            set_nickname(login, val, db_path=db)
            current[login] = val

    _print_nicknames(logins, current)

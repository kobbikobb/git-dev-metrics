from pathlib import Path

import typer

from ..cache import default_db_path


def clear(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Delete the entire local cache database."""
    path = db or default_db_path()

    if not path.exists():
        typer.echo(f"Cache already empty ({path}).")
        return

    if not yes and not typer.confirm(f"Delete {path}?"):
        typer.echo("Cancelled.")
        raise typer.Exit(code=1)

    path.unlink()
    typer.echo(f"Deleted {path}.")

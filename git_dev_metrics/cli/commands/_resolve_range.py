from collections.abc import Callable
from pathlib import Path

import typer

from ...metrics.loader import InvalidRangeError, load_snapshot_for_range
from ...metrics.snapshot import MetricsSnapshot


def resolve_range(
    from_: str | None,
    to: str | None,
    db_path: Path | None,
    wizard: Callable[..., None],
) -> MetricsSnapshot:
    if from_ is None and to is None:
        wizard(db_path=db_path)
        raise typer.Exit()

    if from_ is None or to is None:
        typer.secho(
            "Provide both --from and --to, or neither (for the wizard).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        snapshot = load_snapshot_for_range(from_, to, db_path)
    except InvalidRangeError:
        typer.secho("--to must be >= --from.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from None

    if snapshot is None:
        typer.secho(
            f"No synced data for {from_} to {to}. Run pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    return snapshot

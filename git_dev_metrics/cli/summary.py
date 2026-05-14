from collections.abc import Callable
from pathlib import Path

import typer

from ..metrics.loader import InvalidRangeError, load_snapshot_for_months, load_snapshot_for_range
from ..metrics.printer import ConsolePrinter
from ._wizard import _prompt_months, pick_months

YearMonth = tuple[int, int]


def summary(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Print the dashboard summary to the console."""
    if from_ is None and to is None:
        _summary_wizard(db_path=db)
        return

    if from_ is None or to is None:
        typer.secho(
            "Provide both --from and --to, or neither (for the wizard).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        snapshot = load_snapshot_for_range(from_, to, db)
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

    period_slug = f"{from_}-to-{to}"
    since = snapshot.period.since.strftime("%Y-%m-%d")
    until = snapshot.period.until.strftime("%Y-%m-%d")
    ConsolePrinter().print_combined_metrics(snapshot, period_slug, f"{since} to {until}")


def _summary_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Pick months from cache, print aggregated summary to console."""
    selected = pick_months(db_path, ask_months)
    snapshot = load_snapshot_for_months(selected, db_path)
    if snapshot is None:
        typer.secho("No PRs in selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    first, last = selected[0], selected[-1]
    period_slug = f"{first[0]:04d}-{first[1]:02d}-to-{last[0]:04d}-{last[1]:02d}"
    since = snapshot.period.since.strftime("%Y-%m-%d")
    until = snapshot.period.until.strftime("%Y-%m-%d")
    ConsolePrinter().print_combined_metrics(snapshot, period_slug, f"{since} to {until}")

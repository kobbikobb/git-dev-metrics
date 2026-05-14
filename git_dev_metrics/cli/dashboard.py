from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import typer

from ..metrics import MetricsSnapshot
from ..metrics.loader import InvalidRangeError, load_snapshot_for_months, load_snapshot_for_range
from ..metrics.printer.html import FileHtmlPrinter
from ._browser import open_in_browser
from ._wizard import _prompt_months, pick_months

YearMonth = tuple[int, int]


def _default_output(period_slug: str) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path(f"./metrics_results/dashboard_{ts}_{period_slug}.html")


def _write_and_open_dashboard(
    snapshot: MetricsSnapshot, period_slug: str, date_range: str, output: Path | None
) -> None:
    out = (output or _default_output(period_slug)).with_suffix(".html")
    FileHtmlPrinter(out).print_combined_metrics(snapshot, period_slug, date_range)
    typer.echo(f"Dashboard written to {out}.")
    open_in_browser(out)


def dashboard(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Render the in-depth HTML dashboard and open it in the browser."""
    if from_ is None and to is None:
        _dashboard_wizard(db_path=db)
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
    _write_and_open_dashboard(snapshot, period_slug, f"{since} to {until}", output)


def _dashboard_wizard(
    db_path: Path | None = None,
    *,
    ask_months: Callable[[list[YearMonth]], list[YearMonth]] = _prompt_months,
) -> None:
    """Pick months from cache, render HTML dashboard, open in browser."""
    selected = pick_months(db_path, ask_months)
    snapshot = load_snapshot_for_months(selected, db_path)
    if snapshot is None:
        typer.secho("No PRs in selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    first, last = selected[0], selected[-1]
    period_slug = f"{first[0]:04d}-{first[1]:02d}-to-{last[0]:04d}-{last[1]:02d}"
    since = snapshot.period.since.strftime("%Y-%m-%d")
    until = snapshot.period.until.strftime("%Y-%m-%d")
    _write_and_open_dashboard(snapshot, period_slug, f"{since} to {until}", output=None)

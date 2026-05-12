from pathlib import Path

import typer

from ..cache import load_all_repos_for_range
from ..metrics.analyzer import build_combined_metrics_for_repos
from ..utils.date_utils import month_iter, range_period
from ._month_arg import parse_month_arg
from .report_runner import render_combined
from .report_wizard import report_wizard

_DATE_FMT = "%Y-%m-%d"


def report(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output file path (.md or .html)"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
    open_browser: bool = typer.Option(
        True, "--open/--no-open", help="Open HTML in browser after writing."
    ),
) -> None:
    """Render the dashboard for all cached repos across a month range."""
    if from_ is None and to is None:
        report_wizard(db_path=db)
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
    repo_prs = load_all_repos_for_range(months, db_path=db)
    if not repo_prs:
        typer.secho(
            f"No synced data for {from_} to {to}. Run gdm pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    period = range_period(from_ym, to_ym)
    metrics = build_combined_metrics_for_repos(repo_prs, period)
    period_slug = f"{from_}-to-{to}"
    date_range = f"{period.since.strftime(_DATE_FMT)} to {period.until.strftime(_DATE_FMT)}"
    render_combined(metrics, period_slug, date_range, output, open_browser=open_browser)

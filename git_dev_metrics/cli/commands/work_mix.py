from pathlib import Path

import typer

from ...metrics.printer._html_templates import render_template
from ...metrics.work_mix import monthly_work_mix
from ...utils.date_utils import last_n_months, month_iter, month_key
from .._browser import open_in_browser
from .._month_arg import parse_month_arg
from .._options import DB_OPTION


def _months(from_: str | None, to: str | None) -> list[str]:
    if from_ is None and to is None:
        start, end = last_n_months(12, include_current=True)
    elif from_ is not None and to is not None:
        start, end = parse_month_arg(from_, "--from"), parse_month_arg(to, "--to")
    else:
        raise typer.BadParameter("Provide both --from and --to.")
    if start > end:
        raise typer.BadParameter("--to must be on or after --from.")
    return [month_key(y, m) for y, m in month_iter(start, end)]


def work_mix(
    from_: str | None = typer.Option(None, "--from", help="First month (YYYY-MM)."),
    to: str | None = typer.Option(None, "--to", help="Last month (YYYY-MM)."),
    repo: list[str] | None = typer.Option(None, help="Limit to owner/repo. Repeat for more."),
    output: Path | None = typer.Option(None, help="Output HTML path."),
    db: Path | None = DB_OPTION,
) -> None:
    """Chart monthly merged PR counts and shares by work category for each repository."""
    months = _months(from_, to)
    repos = monthly_work_mix(months[0], months[-1], db)
    if repo:
        selected = {name.lower() for name in repo}
        if missing := selected.difference(repos):
            raise typer.BadParameter(f"No synced months for {', '.join(sorted(missing))}.")
        repos = {name: data for name, data in repos.items() if name in selected}
    if not repos:
        raise typer.BadParameter("No synced repositories in this period. Run pull first.")
    path = output or Path(f"metrics_results/work_mix_{months[0]}_{months[-1]}.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_template("work_mix.html", months=months, repos=repos), encoding="utf-8")
    typer.echo(f"Monthly PR work mix written to {path}.")
    open_in_browser(path)

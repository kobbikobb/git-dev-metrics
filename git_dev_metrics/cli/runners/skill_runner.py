from datetime import datetime
from pathlib import Path

import typer

from ...cache import list_synced_months
from ...github.auth_cache import load_token
from ...github.queries import fetch_skill_report_prs
from ...metrics.printer.skill import FileSkillPrinter
from ...metrics.skill_calculator import build_skill_dataset
from .._browser import open_in_browser

YearMonth = tuple[int, int]


def _default_output(months: list[YearMonth]) -> Path:
    first, last = months[0], months[-1]
    return Path(
        f"./metrics_results/skill_{first[0]:04d}-{first[1]:02d}_to_{last[0]:04d}-{last[1]:02d}.html"
    )


def perform_skill_report(
    months: list[YearMonth], output: Path | None, db_path: Path | None
) -> None:
    token = load_token()
    if not token:
        typer.secho("No GitHub token found. Run login first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    synced = list_synced_months(db_path=db_path)
    wanted = set(months)
    all_prs: list[dict] = []
    seen_ids: set[int] = set()

    for org, repo, year, month in synced:
        if (year, month) not in wanted:
            continue
        for pr in fetch_skill_report_prs(token, org, repo, year, month):
            n = pr["number"]
            if n not in seen_ids:
                seen_ids.add(n)
                all_prs.append(pr)

    if not all_prs:
        typer.secho("No PRs found for selected months.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    dataset = build_skill_dataset(all_prs)
    first, last = months[0], months[-1]
    period_range = (
        f"{datetime(first[0], first[1], 1).strftime('%b %Y')}"
        f" – {datetime(last[0], last[1], 1).strftime('%b %Y')}"
    )
    out_path = output or _default_output(months)
    FileSkillPrinter(out_path).render(dataset, period_range)
    typer.echo(f"Skill report written to {out_path}.")
    open_in_browser(out_path)

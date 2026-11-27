from datetime import datetime
from pathlib import Path

import typer

from ...cache import get_hidden_logins
from ...github.queries import fetch_skill_report_prs
from ...metrics.printer.skill import FileSkillPrinter
from ...metrics.skill_calculator import build_skill_dataset
from .._browser import open_in_browser
from ._report_prs import load_report_prs

YearMonth = tuple[int, int]


def _default_output(months: list[YearMonth]) -> Path:
    first, last = months[0], months[-1]
    return Path(
        f"./metrics_results/skill_{first[0]:04d}-{first[1]:02d}_to_{last[0]:04d}-{last[1]:02d}.html"
    )


def perform_skill_report(
    months: list[YearMonth], output: Path | None, db_path: Path | None
) -> None:
    all_prs = load_report_prs(months, db_path, fetch_skill_report_prs)
    dataset = build_skill_dataset(all_prs)
    first, last = months[0], months[-1]
    period_range = (
        f"{datetime(first[0], first[1], 1).strftime('%b %Y')}"
        f" – {datetime(last[0], last[1], 1).strftime('%b %Y')}"
    )
    out_path = output or _default_output(months)
    FileSkillPrinter(out_path).render(
        dataset, period_range, hidden_logins=get_hidden_logins(db_path=db_path)
    )
    typer.echo(f"Skill report written to {out_path}.")
    open_in_browser(out_path)

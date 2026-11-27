from datetime import datetime
from pathlib import Path

import typer

from ...cache import get_hidden_logins
from ...github.queries import fetch_lang_report_prs
from ...metrics.lang_calculator import build_lang_dataset
from ...metrics.printer.lang import FileLangPrinter
from .._browser import open_in_browser
from ._report_prs import load_report_prs

YearMonth = tuple[int, int]


def _default_output(months: list[YearMonth]) -> Path:
    first, last = months[0], months[-1]
    return Path(
        f"./metrics_results/lang_{first[0]:04d}-{first[1]:02d}_to_{last[0]:04d}-{last[1]:02d}.html"
    )


def perform_lang_report(months: list[YearMonth], output: Path | None, db_path: Path | None) -> None:
    all_prs = load_report_prs(months, db_path, fetch_lang_report_prs)
    dataset = build_lang_dataset(all_prs)
    first, last = months[0], months[-1]
    period_range = (
        f"{datetime(first[0], first[1], 1).strftime('%b %Y')}"
        f" – {datetime(last[0], last[1], 1).strftime('%b %Y')}"
    )
    out_path = output or _default_output(months)
    FileLangPrinter(out_path).render(
        dataset, period_range, hidden_logins=get_hidden_logins(db_path=db_path)
    )
    typer.echo(f"Language report written to {out_path}.")
    open_in_browser(out_path)

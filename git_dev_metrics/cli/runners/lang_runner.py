from datetime import datetime
from pathlib import Path

import typer

from ...metrics.printer.lang import FileLangPrinter
from .._browser import open_in_browser
from ._report_prs import load_lang_report

YearMonth = tuple[int, int]


def _default_output(months: list[YearMonth]) -> Path:
    first, last = months[0], months[-1]
    return Path(
        f"./metrics_results/lang_{first[0]:04d}-{first[1]:02d}_to_{last[0]:04d}-{last[1]:02d}.html"
    )


def perform_lang_report(months: list[YearMonth], output: Path | None, db_path: Path | None) -> None:
    dataset = load_lang_report(months, db_path)
    first, last = months[0], months[-1]
    period_range = (
        f"{datetime(first[0], first[1], 1).strftime('%b %Y')}"
        f" – {datetime(last[0], last[1], 1).strftime('%b %Y')}"
    )
    out_path = output or _default_output(months)
    FileLangPrinter(out_path).render(dataset, period_range)
    typer.echo(f"Language report written to {out_path}.")
    open_in_browser(out_path)

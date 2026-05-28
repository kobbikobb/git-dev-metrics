from pathlib import Path

from ..runners.lang_runner import perform_lang_report
from ._wizard import pick_months


def lang_wizard(db_path: Path | None = None) -> None:
    selected = pick_months(db_path)
    perform_lang_report(selected, output=None, db_path=db_path)

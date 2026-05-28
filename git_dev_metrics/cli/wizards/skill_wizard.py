from pathlib import Path

from ..runners.skill_runner import perform_skill_report
from ._wizard import pick_months


def skill_wizard(db_path: Path | None = None) -> None:
    selected = pick_months(db_path)
    perform_skill_report(selected, output=None, db_path=db_path)

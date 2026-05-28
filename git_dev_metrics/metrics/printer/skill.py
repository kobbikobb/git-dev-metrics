from pathlib import Path

from ..skill_calculator import SkillDataset
from ._html_templates import render_template


class FileSkillPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, dataset: SkillDataset, period_range: str) -> None:
        render_template(
            "skill.html",
            period_range=period_range,
            devs=dataset.devs,
            skills=dataset.skills,
            dev_skills={k: dict(v) for k, v in dataset.dev_skills.items()},
            team_skills=dataset.team_skills,
        )


__all__ = ["FileSkillPrinter"]

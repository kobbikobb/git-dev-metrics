from pathlib import Path

from ..skill_calculator import SkillDataset
from ._html_templates import render_template


class FileSkillPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, dataset: SkillDataset, period_range: str) -> None:
        html = render_template(
            "skill.html",
            period_range=period_range,
            devs=dataset.devs,
            skills=sorted(dataset.team_skills),
            team_skills=dataset.team_skills,
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileSkillPrinter"]

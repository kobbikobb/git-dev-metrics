from collections.abc import Set
from pathlib import Path

from ..skill_calculator import SkillDataset
from ._html_templates import render_template


class FileSkillPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(
        self, dataset: SkillDataset, period_range: str, *, hidden_logins: Set[str] = frozenset()
    ) -> None:
        devs = [dev for dev in dataset.devs if dev.lower() not in hidden_logins]
        html = render_template(
            "skill.html",
            period_range=period_range,
            devs=devs,
            skills=dataset.skills,
            dev_skills={dev: dict(dataset.dev_skills[dev]) for dev in devs},
            team_skills=dataset.team_skills,
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileSkillPrinter"]

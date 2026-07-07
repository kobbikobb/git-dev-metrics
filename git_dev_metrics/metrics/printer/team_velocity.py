from pathlib import Path

from ..team_velocity_calculator import TeamVelocityDataset
from ._html_templates import render_template


class FileTeamVelocityPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, dataset: TeamVelocityDataset, period_range: str) -> None:
        html = render_template(
            "team_velocity.html",
            period_range=period_range,
            months=dataset.months,
            repos=dataset.repos,
            repo_pr_counts=dataset.repo_pr_counts,
            active_devs=dataset.active_devs,
            prs_per_dev=dataset.prs_per_dev,
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTeamVelocityPrinter"]

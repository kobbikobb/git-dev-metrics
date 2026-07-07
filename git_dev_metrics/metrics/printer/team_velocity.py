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
            month_labels=[m.month_label for m in dataset.months],
            pr_counts=[m.pr_count for m in dataset.months],
            active_devs=[m.active_devs for m in dataset.months],
            prs_per_dev=[m.prs_per_dev for m in dataset.months],
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTeamVelocityPrinter"]

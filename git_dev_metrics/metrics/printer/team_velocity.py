from pathlib import Path

from ..team_velocity_calculator import TeamVelocityDataset
from ._html_templates import render_template


class FileTeamVelocityPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(
        self,
        dataset: TeamVelocityDataset,
        period_range: str,
        nicknames: dict[str, str] | None = None,
    ) -> None:
        raw_names = sorted(dataset.dev_month_counts[0].keys()) if dataset.dev_month_counts else []
        resolve = (nicknames or {}).get
        dev_names = [resolve(n, n) for n in raw_names]
        dev_data = [
            [month_counts[dev] for month_counts in dataset.dev_month_counts] for dev in dev_names
        ]
        html = render_template(
            "team_velocity.html",
            period_range=period_range,
            month_labels=[m.month_label for m in dataset.months],
            pr_counts=[m.pr_count for m in dataset.months],
            active_devs=[m.active_devs for m in dataset.months],
            prs_per_dev=[m.prs_per_dev for m in dataset.months],
            dev_names=dev_names,
            dev_data=dev_data,
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTeamVelocityPrinter"]

from collections.abc import Set
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
        *,
        nicknames: dict[str, str] | None = None,
        hidden_logins: Set[str] = frozenset(),
    ) -> None:
        month_labels = [m.month_label for m in dataset.months]

        dev_data: list[dict[str, str | list[int]]] = []
        if dataset.dev_month_counts:
            names = {login.lower(): name for login, name in (nicknames or {}).items()}
            logins = sorted(dataset.dev_month_counts[0].keys())
            dev_data = [
                {
                    "label": names.get(login.lower(), login),
                    "data": [m.get(login, 0) for m in dataset.dev_month_counts],
                }
                for login in logins
                if login.lower() not in hidden_logins
            ]

        html = render_template(
            "team_velocity.html",
            period_range=period_range,
            month_labels=month_labels,
            pr_counts=[m.pr_count for m in dataset.months],
            active_devs=[m.active_devs for m in dataset.months],
            prs_per_dev=[m.prs_per_dev for m in dataset.months],
            dev_data=dev_data,
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTeamVelocityPrinter"]

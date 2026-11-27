from collections.abc import Set
from dataclasses import asdict
from pathlib import Path
from typing import TypedDict

from ..trend_calculator import DevMonthDict, TrendDataset
from ._html_templates import render_template


class _TrendData(TypedDict):
    months: list[str]
    devs: list[str]
    rows: dict[str, list[DevMonthDict]]


def _to_dict(dataset: TrendDataset, hidden_logins: Set[str]) -> _TrendData:
    devs = [dev for dev in dataset.devs if dev.lower() not in hidden_logins]
    return _TrendData(
        months=dataset.months,
        devs=devs,
        rows={dev: [DevMonthDict(**asdict(r)) for r in dataset.rows[dev]] for dev in devs},
    )


class FileTrendPrinter:
    """Render the self-contained trend HTML report."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, dataset: TrendDataset, *, hidden_logins: Set[str] = frozenset()) -> None:
        period_range = f"{dataset.months[0]} to {dataset.months[-1]}" if dataset.months else ""
        html = render_template(
            "trend.html", period_range=period_range, dataset=_to_dict(dataset, hidden_logins)
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTrendPrinter"]

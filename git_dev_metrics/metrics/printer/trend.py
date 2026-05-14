from dataclasses import asdict
from pathlib import Path

from ..trend_calculator import TrendDataset
from ._html_templates import render_template


def _to_dict(dataset: TrendDataset) -> dict:
    return {
        "months": dataset.months,
        "devs": dataset.devs,
        "rows": {dev: [asdict(r) for r in rows] for dev, rows in dataset.rows.items()},
    }


class FileTrendPrinter:
    """Render the self-contained trend HTML report."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, dataset: TrendDataset) -> None:
        period_range = f"{dataset.months[0]} to {dataset.months[-1]}" if dataset.months else ""
        html = render_template("trend.html", period_range=period_range, dataset=_to_dict(dataset))
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTrendPrinter"]

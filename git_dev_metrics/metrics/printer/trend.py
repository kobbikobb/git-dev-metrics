from pathlib import Path

from ..trend_calculator import TrendDataset
from ._html_templates import render_template


class FileTrendPrinter:
    """Render the self-contained trend HTML report."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, dataset: TrendDataset) -> None:
        months = dataset["months"]
        period_range = f"{months[0]} to {months[-1]}" if months else ""
        html = render_template("trend.html", period_range=period_range, dataset=dataset)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTrendPrinter"]

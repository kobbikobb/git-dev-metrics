from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..trend_calculator import TrendDataset

_ENV: Environment | None = None


def _get_env() -> Environment:
    global _ENV
    if _ENV is None:
        _ENV = Environment(
            loader=PackageLoader("git_dev_metrics.metrics.printer", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
    return _ENV


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

    def render(self, dataset: TrendDataset, org: str, repo: str) -> None:
        template = _get_env().get_template("trend.html")
        period_range = f"{dataset.months[0]} to {dataset.months[-1]}" if dataset.months else ""
        html = template.render(
            org=org,
            repo=repo,
            period_range=period_range,
            dataset=_to_dict(dataset),
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileTrendPrinter"]

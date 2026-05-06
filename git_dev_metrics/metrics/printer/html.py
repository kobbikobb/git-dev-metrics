from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..health import calculate_dev_health_score
from ..summary import build_summary
from .base import Printer

_ENV: Environment | None = None


def _get_env() -> Environment:
    global _ENV
    if _ENV is None:
        _ENV = Environment(
            loader=PackageLoader("git_dev_metrics.metrics.printer", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
    return _ENV


def _build_devs_list(metrics: dict) -> list[dict]:
    """Flatten dev_metrics into the row shape the dashboard template expects."""
    all_dev_metrics = list(metrics["dev_metrics"].values())
    devs = []
    for dev, m in metrics["dev_metrics"].items():
        health = calculate_dev_health_score(m, all_dev_metrics)
        devs.append(
            {
                "name": dev,
                "health": health,
                "pickup": m.get("pickup_time", 0),
                "review": m.get("review_time", 0),
                "cycle": m.get("cycle_time", 0),
                "size": int(m.get("pr_size", 0)),
                "prs": int(m.get("pr_count", 0)),
                "prs_week": m.get("prs_per_week", 0),
                "reviews": int(m.get("reviews_given", 0)),
                "ai": int(m.get("ai_percentage", 0)),
            }
        )
    return devs


class FileHtmlPrinter(Printer):
    """Render the self-contained HTML dashboard."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def print_combined_metrics(self, metrics: dict, period: str, date_range: str) -> None:
        env = _get_env()
        template = env.get_template("dashboard.html")

        devs = _build_devs_list(metrics)
        summary = build_summary(metrics)

        html = template.render(devs=devs, summary=summary, period=period, date_range=date_range)

        html_path = self._output_path.with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, "w") as f:
            f.write(html)


__all__ = ["FileHtmlPrinter"]

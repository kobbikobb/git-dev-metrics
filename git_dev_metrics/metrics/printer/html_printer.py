from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..health import calculate_health_score
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
    """Transform metrics dict into a flat list of dev rows for the dashboard.

    Args:
        metrics: Combined metrics dict with dev_metrics key.

    Returns:
        List of dicts with name, health, pickup, review, cycle, size, prs,
        prs_week, reviews, ai fields.
    """
    all_dev_metrics = list(metrics["dev_metrics"].values())
    devs = []
    for dev, m in metrics["dev_metrics"].items():
        health = calculate_health_score(m, all_dev_metrics)
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


def _build_summary(devs: list[dict], metrics: dict) -> dict:
    """Compute summary stats across all devs for the summary cards.

    Args:
        devs: Output of _build_devs_list.
        metrics: Full metrics dict from get_combined_metrics.

    Returns:
        Dict with team_health, total_prs, avg_cycle, avg_pickup,
        total_reviews, ai_adoption.
    """
    active = [d for d in devs if d["health"] > 0]
    repo_metrics = metrics.get("repo_metrics", {})
    total_prs = int(sum(m.get("pr_count", 0) for m in repo_metrics.values()))
    total_reviews = int(sum(m.get("reviews_given", 0) for m in repo_metrics.values()))
    return {
        "team_health": round(sum(d["health"] for d in devs) / len(devs)) if devs else 0,
        "total_prs": total_prs,
        "avg_cycle": round(sum(d["cycle"] for d in active) / len(active), 1) if active else 0,
        "avg_pickup": round(sum(d["pickup"] for d in active) / len(active), 1) if active else 0,
        "total_reviews": total_reviews,
        "ai_adoption": round(
            sum(m.get("ai_percentage", 0) for m in repo_metrics.values()) / len(repo_metrics)
        )
        if repo_metrics
        else 0,
    }


class FileHtmlPrinter(Printer):
    """Print dev metrics dashboard as a self-contained HTML file."""

    def __init__(self, output_path: Path) -> None:
        """Initialize with the base output path (HTML written with .html suffix).

        Args:
            output_path: Base path for output files (e.g. metrics_results/metrics_2026-03-21).
        """
        self._output_path = output_path

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        """Render and write the HTML dashboard to disk.

        Args:
            metrics: Combined metrics dict with dev_metrics.
            period: Time period string (e.g. "30d") for the header.
        """
        env = _get_env()
        template = env.get_template("dashboard.html")

        devs = _build_devs_list(metrics)
        summary = _build_summary(devs, metrics)

        html = template.render(devs=devs, summary=summary, period=period)

        html_path = self._output_path.with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, "w") as f:
            f.write(html)


__all__ = ["FileHtmlPrinter"]

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..health import calculate_dev_health_score
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


def build_summary(metrics: dict) -> dict:
    """Compute summary stats across all devs for the summary cards."""
    all_dev_metrics = list(metrics.get("dev_metrics", {}).values())
    health_by_dev = [calculate_dev_health_score(d, all_dev_metrics) for d in all_dev_metrics]
    team = metrics.get("team_metrics") or {}
    pr_count = int(team.get("pr_count", 0))
    total_reviews = int(team.get("reviews_given", 0))

    raw_counts = metrics.get("reviewer_counts")
    if raw_counts is None:
        raw_counts = {
            dev: m.get("reviews_given", 0) for dev, m in (metrics.get("dev_metrics") or {}).items()
        }
    reviewer_counts = {r: int(c) for r, c in raw_counts.items() if c}
    top_reviewer = ""
    max_review_share = 0
    if total_reviews > 0 and reviewer_counts:
        top_reviewer = max(sorted(reviewer_counts), key=lambda d: reviewer_counts[d])
        max_review_share = round(reviewer_counts[top_reviewer] / total_reviews * 100)

    return {
        "team_health": round(sum(health_by_dev) / len(health_by_dev)) if health_by_dev else 0,
        "total_prs": pr_count,
        "median_cycle": round(team.get("cycle_time", 0), 1),
        "median_pickup": round(team.get("pickup_time", 0), 1),
        "total_reviews": total_reviews,
        "ai_adoption": round(team.get("ai_percentage", 0)),
        "avg_lines_per_pr": round(team.get("avg_lines_per_pr", 0), 1),
        "review_ratio": round(total_reviews / pr_count, 2) if pr_count else 0.0,
        "top_reviewer": top_reviewer,
        "max_review_share": max_review_share,
    }


class FileHtmlPrinter(Printer):
    """Print dev metrics dashboard as a self-contained HTML file."""

    def __init__(self, output_path: Path) -> None:
        """Initialize with the base output path (HTML written with .html suffix).

        Args:
            output_path: Base path for output files (e.g. metrics_results/metrics_2026-03-21).
        """
        self._output_path = output_path

    def print_combined_metrics(self, metrics: dict, period: str, date_range: str) -> None:
        """Render and write the HTML dashboard to disk.

        Args:
            metrics: Combined metrics dict with dev_metrics.
            period: Time period string (e.g. "30d") for the header.
            date_range: Date range string (e.g. "2026-01-01 to 2026-01-31").
        """
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

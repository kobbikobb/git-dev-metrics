from pathlib import Path

from ..snapshot import MetricsSnapshot
from ._html_templates import render_template
from .base import Printer


def _devs_for_template(snapshot: MetricsSnapshot) -> list[dict]:
    return [
        {
            "name": row.name,
            "health": row.health,
            "pickup": row.pickup_time,
            "review": row.review_time,
            "cycle": row.cycle_time,
            "size": int(row.pr_size),
            "prs": row.pr_count,
            "prs_week": row.prs_per_week,
            "reviews": row.reviews_given,
            "ai": int(row.ai_percentage),
        }
        for row in snapshot.devs
    ]


def _summary_for_template(snapshot: MetricsSnapshot) -> dict:
    team = snapshot.team
    summary = snapshot.summary
    return {
        "team_health": team.health,
        "total_prs": team.pr_count,
        "median_lines_per_pr": round(team.pr_size, 1),
        "median_cycle": round(team.cycle_time, 1),
        "median_pickup": round(team.pickup_time, 1),
        "median_prs_per_week": round(team.prs_per_week, 2),
        "total_reviews": team.reviews_given,
        "ai_adoption": round(team.ai_percentage),
        "ai_per_dev": list(summary.ai_per_dev),
        "review_ratio": summary.review_ratio,
        "top_reviewer": summary.top_reviewer,
        "max_review_share": summary.max_review_share,
    }


class FileHtmlPrinter(Printer):
    """Render the self-contained HTML dashboard."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def print_combined_metrics(
        self, snapshot: MetricsSnapshot, period: str, date_range: str
    ) -> None:
        html = render_template(
            "dashboard.html",
            devs=_devs_for_template(snapshot),
            summary=_summary_for_template(snapshot),
            period=period,
            date_range=date_range,
        )

        html_path = self._output_path.with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(html_path, "w") as f:
            f.write(html)


__all__ = ["FileHtmlPrinter"]

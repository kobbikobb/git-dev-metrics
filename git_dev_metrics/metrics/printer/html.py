from pathlib import Path
from typing import TypedDict

from ..snapshot import MetricsSnapshot
from ._html_templates import render_template


class _DevRow(TypedDict):
    name: str
    health: int
    pickup: float
    review: float
    cycle: float
    size: int
    prs: int
    prs_week: float
    reviews: int
    ai: int


class _SummaryData(TypedDict):
    team_health: int
    total_prs: int
    median_lines_per_pr: float
    median_cycle: float
    median_pickup: float
    median_prs_per_week: float
    total_reviews: int
    ai_adoption: int
    ai_per_dev: list[int]
    review_ratio: float
    top_reviewer: str
    max_review_share: int


def _devs_for_template(
    snapshot: MetricsSnapshot,
    nicknames: dict[str, str] | None = None,
) -> list[_DevRow]:
    return [
        _DevRow(
            name=nicknames.get(row.name, row.name) if nicknames else row.name,
            health=row.health,
            pickup=row.pickup_time,
            review=row.review_time,
            cycle=row.cycle_time,
            size=int(row.pr_size),
            prs=row.pr_count,
            prs_week=row.prs_per_week,
            reviews=row.reviews_given,
            ai=int(row.ai_percentage),
        )
        for row in snapshot.devs
    ]


def _summary_for_template(
    snapshot: MetricsSnapshot,
    nicknames: dict[str, str] | None = None,
) -> _SummaryData:
    team = snapshot.team
    summary = snapshot.summary
    top_reviewer = summary.top_reviewer
    if nicknames and top_reviewer:
        top_reviewer = nicknames.get(top_reviewer, top_reviewer)
    elif not top_reviewer:
        top_reviewer = "\u2014"
    return _SummaryData(
        team_health=team.health,
        total_prs=team.pr_count,
        median_lines_per_pr=round(team.pr_size, 1),
        median_cycle=round(team.cycle_time, 1),
        median_pickup=round(team.pickup_time, 1),
        median_prs_per_week=round(team.prs_per_week, 2),
        total_reviews=team.reviews_given,
        ai_adoption=round(team.ai_percentage),
        ai_per_dev=list(summary.ai_per_dev),
        review_ratio=summary.review_ratio,
        top_reviewer=top_reviewer,
        max_review_share=summary.max_review_share,
    )


class FileHtmlPrinter:
    """Render the self-contained HTML dashboard."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def print_combined_metrics(
        self,
        snapshot: MetricsSnapshot,
        period: str,
        date_range: str,
        nicknames: dict[str, str] | None = None,
    ) -> None:
        html = render_template(
            "dashboard.html",
            devs=_devs_for_template(snapshot, nicknames),
            summary=_summary_for_template(snapshot, nicknames),
            period=period,
            date_range=date_range,
            has_partial=snapshot.has_partial,
        )

        html_path = self._output_path.with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        with html_path.open("w") as f:
            f.write(html)


__all__ = ["FileHtmlPrinter"]

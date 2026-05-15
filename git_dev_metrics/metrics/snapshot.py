"""Frozen, fully-computed metrics for one period across one or more repos.

Built once via `MetricsSnapshot.from_repo_prs`. Printers consume snapshots;
they do not recompute health, bands, sort orders, or aggregations.
"""

from dataclasses import dataclass
from typing import Literal

from ..models import PullRequest
from ..utils import TimePeriod, period_days
from ._dev_repo_metrics import compute_dev_metrics, compute_repo_metrics
from .calculator import calculate_reviews_given
from .health import calculate_dev_health_score, calculate_health_score

# Imports from _health_ranking must come after Row/Band definitions
# to resolve circular dependency (_health_ranking imports Row/Band).

Band = Literal["good", "ok", "bad"]

_BAND_COLOR: dict[Band, str] = {"good": "green", "ok": "yellow", "bad": "red"}


def band_color(band: Band) -> str:
    return _BAND_COLOR[band]


@dataclass(frozen=True)
class Row:
    name: str
    pr_count: int
    cycle_time: float
    pickup_time: float
    review_time: float
    pr_size: float
    avg_lines_per_pr: float
    prs_per_week: float
    reviews_given: int
    ai_percentage: float
    health: int
    band: Band


@dataclass(frozen=True)
class Summary:
    ai_per_dev: tuple[int, ...]
    review_ratio: float
    top_reviewer: str
    max_review_share: int


from ._health_ranking import (  # noqa: E402
    band_from_health,
    compute_team_row,
    rank_rows,
)


@dataclass(frozen=True)
class MetricsSnapshot:
    period: TimePeriod
    team: Row
    devs: tuple[Row, ...]
    repos: tuple[Row, ...]
    summary: Summary
    reviewer_counts: dict[str, int]

    @classmethod
    def from_repo_prs(
        cls,
        repo_prs: dict[str, list[PullRequest]],
        period: TimePeriod,
    ) -> MetricsSnapshot:
        days = period_days(period)
        all_prs: list[PullRequest] = [pr for prs in repo_prs.values() for pr in prs]
        reviewer_counts = calculate_reviews_given(all_prs)

        dev_raw_data = compute_dev_metrics(all_prs, days, reviewer_counts)
        devs = rank_rows(dev_raw_data, calculate_dev_health_score)

        repo_raw_data = compute_repo_metrics(repo_prs, days)
        repos = rank_rows(repo_raw_data, calculate_health_score)

        team = compute_team_row(all_prs, days, dev_raw_data, devs, reviewer_counts)

        return cls(
            period=period,
            team=team,
            devs=devs,
            repos=repos,
            summary=build_summary(devs, reviewer_counts, team),
            reviewer_counts=reviewer_counts,
        )


def build_summary(
    devs: tuple[Row, ...],
    reviewer_counts: dict[str, int],
    team: Row,
) -> Summary:
    ai_per_dev = tuple(sorted(int(r.ai_percentage) for r in devs))
    total_reviews = team.reviews_given
    pr_count = team.pr_count

    filtered_reviewers = {r: int(c) for r, c in reviewer_counts.items() if c}
    top_reviewer = ""
    max_review_share = 0
    if total_reviews > 0 and filtered_reviewers:
        top_reviewer = max(sorted(filtered_reviewers), key=lambda d: filtered_reviewers[d])
        max_review_share = round(filtered_reviewers[top_reviewer] / total_reviews * 100)

    return Summary(
        ai_per_dev=ai_per_dev,
        review_ratio=round(total_reviews / pr_count, 2) if pr_count else 0.0,
        top_reviewer=top_reviewer,
        max_review_share=max_review_share,
    )


__all__ = [
    "Band",
    "MetricsSnapshot",
    "Row",
    "Summary",
    "band_color",
    "band_from_health",
    "build_summary",
]

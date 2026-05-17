"""Frozen, fully-computed metrics for one period across one or more repos.

Built once via `MetricsSnapshot.from_repo_prs`. Printers consume snapshots;
they do not recompute health, bands, sort orders, or aggregations.
"""

from dataclasses import dataclass

from ..models import PullRequest
from ..utils import TimePeriod, period_days
from ._dev_repo_metrics import compute_dev_metrics, compute_raw, compute_repo_metrics
from ._health_ranking import band_from_health, rank_rows, raw_to_row
from ._raw_metrics import RawMetrics
from ._rows import Row, Summary
from .calculator import calculate_reviews_given, median
from .health import calculate_dev_health_score, calculate_health_score

_PER_DEV_AGGREGATED_KEYS = (
    "cycle_time",
    "pickup_time",
    "review_time",
    "pr_size",
    "avg_lines_per_pr",
    "prs_per_week",
)


def compute_team_row(
    all_prs: list[PullRequest],
    days: int,
    dev_raws: dict[str, RawMetrics],
    devs: tuple[Row, ...],
    reviewer_counts: dict[str, int],
) -> Row:
    team_raw = compute_raw(all_prs, days, sum(reviewer_counts.values()))
    aggregated = {
        key: round(median([getattr(m, key) for m in dev_raws.values() if getattr(m, key, None)]), 2)
        for key in _PER_DEV_AGGREGATED_KEYS
    }
    ai_values = [m.ai_percentage for m in dev_raws.values()]
    aggregated["ai_percentage"] = round(sum(ai_values) / len(ai_values), 1) if ai_values else 0.0
    team_health = round(sum(r.health for r in devs) / len(devs)) if devs else 0
    return raw_to_row(
        "team",
        RawMetrics(
            **aggregated,
            pr_count=team_raw.pr_count,
            reviews_given=team_raw.reviews_given,
        ),
        team_health,
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
    "MetricsSnapshot",
    "band_from_health",
    "build_summary",
    "compute_team_row",
]

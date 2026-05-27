"""Frozen, fully-computed metrics for one period across one or more repos.

Built once via `MetricsSnapshot.from_repo_prs`. Printers consume snapshots;
they do not recompute health, bands, sort orders, or aggregations.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ..models import PullRequest
from ..utils import TimePeriod, period_days
from ._ai_detection import calculate_ai_percentage
from ._rows import Band, RawMetrics, Row, Summary
from .calculator import (
    calculate_avg_lines_per_pr,
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_reviews_given,
    calculate_throughput,
    group_prs_by_devs,
    median,
)
from .health import calculate_dev_health_score, calculate_health_score


def compute_raw(prs: list[PullRequest], days: int, reviews_given: int) -> RawMetrics:
    return RawMetrics(
        cycle_time=calculate_cycle_time(prs),
        pr_size=calculate_pr_size(prs),
        avg_lines_per_pr=calculate_avg_lines_per_pr(prs),
        pr_count=calculate_throughput(prs),
        pickup_time=calculate_pickup_time(prs),
        review_time=calculate_review_time(prs),
        prs_per_week=calculate_prs_per_week(prs, days),
        reviews_given=reviews_given,
        ai_percentage=calculate_ai_percentage(prs),
    )


def compute_dev_metrics(
    all_prs: list[PullRequest], days: int, reviewer_counts: dict[str, int]
) -> dict[str, RawMetrics]:
    return {
        dev: compute_raw(dev_prs, days, reviewer_counts.get(dev, 0))
        for dev, dev_prs in group_prs_by_devs(all_prs).items()
    }


def compute_repo_metrics(
    repo_prs: dict[str, list[PullRequest]], days: int
) -> dict[str, RawMetrics]:
    raws: dict[str, RawMetrics] = {}
    for name, prs in repo_prs.items():
        reviews_given = sum(calculate_reviews_given(prs).values())
        raw = compute_raw(prs, days, reviews_given)
        if raw.pr_count > 0:
            raws[name] = raw
    return raws


def band_from_health(health: int) -> Band:
    if health >= 80:
        return "good"
    if health >= 60:
        return "ok"
    return "bad"


def raw_to_row(name: str, raw: RawMetrics, health: int) -> Row:
    return Row(
        name=name,
        pr_count=raw.pr_count,
        cycle_time=raw.cycle_time,
        pickup_time=raw.pickup_time,
        review_time=raw.review_time,
        pr_size=raw.pr_size,
        avg_lines_per_pr=raw.avg_lines_per_pr,
        prs_per_week=raw.prs_per_week,
        reviews_given=raw.reviews_given,
        ai_percentage=raw.ai_percentage,
        health=health,
        band=band_from_health(health),
    )


def rank_rows(
    raws: dict[str, RawMetrics],
    health_fn: Callable[[RawMetrics, list[RawMetrics]], int],
) -> tuple[Row, ...]:
    cohort = list(raws.values())
    rows = [raw_to_row(name, m, health_fn(m, cohort)) for name, m in raws.items()]
    rows.sort(key=lambda r: r.health, reverse=True)
    return tuple(rows)


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
    has_partial: bool = False

    @classmethod
    def from_repo_prs(
        cls,
        repo_prs: dict[str, list[PullRequest]],
        period: TimePeriod,
        *,
        has_partial: bool = False,
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
            has_partial=has_partial,
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

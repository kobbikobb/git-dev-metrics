from typing import Any

from ..models import PullRequest
from .calculator import (
    calculate_ai_percentage,
    calculate_avg_lines_per_pr,
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_reviews_given,
    calculate_throughput,
    group_prs_by_devs,
)


def compute_metrics_dict(prs: list[PullRequest], days: int, reviews_given: int) -> dict[str, Any]:
    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "avg_lines_per_pr": calculate_avg_lines_per_pr(prs),
        "pr_count": calculate_throughput(prs),
        "pickup_time": calculate_pickup_time(prs),
        "review_time": calculate_review_time(prs),
        "prs_per_week": calculate_prs_per_week(prs, days),
        "reviews_given": reviews_given,
        "ai_percentage": calculate_ai_percentage(prs),
    }


def compute_dev_metrics(
    all_prs: list[PullRequest], days: int, reviewer_counts: dict[str, int]
) -> dict[str, dict[str, Any]]:
    return {
        dev: compute_metrics_dict(dev_prs, days, reviewer_counts.get(dev, 0))
        for dev, dev_prs in group_prs_by_devs(all_prs).items()
    }


def compute_repo_metrics(
    repo_prs: dict[str, list[PullRequest]], days: int
) -> dict[str, dict[str, Any]]:
    raws: dict[str, dict[str, Any]] = {}
    for name, prs in repo_prs.items():
        reviews_given = sum(calculate_reviews_given(prs).values())
        raw = compute_metrics_dict(prs, days, reviews_given)
        if raw["pr_count"] > 0:
            raws[name] = raw
    return raws

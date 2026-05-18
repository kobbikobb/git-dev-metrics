"""Typed raw metrics from the compute pipeline before health scoring."""

from dataclasses import dataclass

from ..models import PullRequest
from .calculator import (
    calculate_ai_percentage,
    calculate_avg_lines_per_pr,
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_throughput,
)


@dataclass(frozen=True)
class RawMetrics:
    cycle_time: float
    pickup_time: float
    review_time: float
    pr_size: float
    avg_lines_per_pr: float
    pr_count: int
    prs_per_week: float
    reviews_given: int
    ai_percentage: float


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

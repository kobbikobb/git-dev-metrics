"""Typed raw metrics from the compute pipeline before health scoring."""

from dataclasses import dataclass


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

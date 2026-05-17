"""Shared row types used by snapshot and health ranking.

Leaf module — no dependencies within the metrics package.
"""

from dataclasses import dataclass
from typing import Literal

Band = Literal["good", "ok", "bad"]

_BAND_COLOR: dict[Band, str] = {"good": "green", "ok": "yellow", "bad": "red"}


def band_color(band: Band) -> str:
    return _BAND_COLOR[band]


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
class StalePr:
    number: int
    title: str
    author: str | None
    repo: str
    age_hours: float
    age_days: float
    is_draft: bool
    is_approved: bool
    url: str


@dataclass(frozen=True)
class Summary:
    ai_per_dev: tuple[int, ...]
    review_ratio: float
    top_reviewer: str
    max_review_share: int

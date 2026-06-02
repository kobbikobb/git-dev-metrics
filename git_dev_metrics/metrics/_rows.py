"""Shared row types used across the metrics pipeline.

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


_TEAM_TARGETS: dict[str, tuple[str, str]] = {
    "cycle_time_max": ("Cycle Time", "h"),
    "pickup_time_max": ("Pickup Time", "h"),
    "review_time_max": ("Review Time", "h"),
    "health_min": ("Health", ""),
    "prs_per_week_min": ("PRs/Week", ""),
}


def team_target_status(team: Row, targets: dict[str, float]) -> dict:
    """Compare team row against targets, return {items, met, total}."""
    items: list[dict] = []
    met = 0
    for key, (label, unit) in _TEAM_TARGETS.items():
        if key not in targets:
            continue
        target = targets[key]
        actual = getattr(team, key.removesuffix("_max").removesuffix("_min"), None)
        if actual is None:
            continue
        is_max = key.endswith("_max")
        ok = actual <= target if is_max else actual >= target
        if ok:
            met += 1
        items.append(
            {
                "label": label,
                "actual": round(actual, 1),
                "target": int(target) if target == int(target) else target,
                "unit": unit,
                "ok": ok,
            }
        )
    return {"items": items, "met": met, "total": len(items)}


@dataclass(frozen=True)
class Summary:
    ai_per_dev: tuple[int, ...]
    review_ratio: float
    top_reviewer: str
    max_review_share: int

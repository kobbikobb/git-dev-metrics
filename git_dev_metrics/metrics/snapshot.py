"""Frozen, fully-computed metrics for one period across one or more repos.

Built once via `MetricsSnapshot.from_repo_prs`. Printers consume snapshots;
they do not recompute health, bands, sort orders, or aggregations.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from ..models import PullRequest
from ..utils import TimePeriod
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
    median,
)
from .health import calculate_dev_health_score, calculate_health_score

Band = Literal["good", "ok", "bad"]

_PER_DEV_AGGREGATED_KEYS = (
    "cycle_time",
    "pickup_time",
    "review_time",
    "pr_size",
    "avg_lines_per_pr",
    "prs_per_week",
)


def _band(health: int) -> Band:
    if health >= 80:
        return "good"
    if health >= 60:
        return "ok"
    return "bad"


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
        period_days = max(1, round((period.until - period.since).total_seconds() / 86400))
        all_prs: list[PullRequest] = [pr for prs in repo_prs.values() for pr in prs]
        reviewer_counts = calculate_reviews_given(all_prs)

        dev_raws = _dev_raws(all_prs, period_days, reviewer_counts)
        devs = _rank(dev_raws, calculate_dev_health_score)

        repo_raws = _active_repo_raws(repo_prs, period_days)
        repos = _rank(repo_raws, calculate_health_score)

        team = _team_row(all_prs, period_days, dev_raws, devs, reviewer_counts)

        return cls(
            period=period,
            team=team,
            devs=devs,
            repos=repos,
            summary=_build_summary(devs, reviewer_counts, team),
            reviewer_counts=reviewer_counts,
        )


def _row_dict(prs: list[PullRequest], period_days: int, reviews_given: int) -> dict[str, Any]:
    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "avg_lines_per_pr": calculate_avg_lines_per_pr(prs),
        "pr_count": calculate_throughput(prs),
        "pickup_time": calculate_pickup_time(prs),
        "review_time": calculate_review_time(prs),
        "prs_per_week": calculate_prs_per_week(prs, period_days),
        "reviews_given": reviews_given,
        "ai_percentage": calculate_ai_percentage(prs),
    }


def _dev_raws(
    all_prs: list[PullRequest], period_days: int, reviewer_counts: dict[str, int]
) -> dict[str, dict[str, Any]]:
    return {
        dev: _row_dict(dev_prs, period_days, reviewer_counts.get(dev, 0))
        for dev, dev_prs in group_prs_by_devs(all_prs).items()
    }


def _active_repo_raws(
    repo_prs: dict[str, list[PullRequest]], period_days: int
) -> dict[str, dict[str, Any]]:
    raws: dict[str, dict[str, Any]] = {}
    for name, prs in repo_prs.items():
        reviews_given = sum(calculate_reviews_given(prs).values())
        raw = _row_dict(prs, period_days, reviews_given)
        if raw["pr_count"] > 0:
            raws[name] = raw
    return raws


def _team_row(
    all_prs: list[PullRequest],
    period_days: int,
    dev_raws: dict[str, dict[str, Any]],
    devs: tuple[Row, ...],
    reviewer_counts: dict[str, int],
) -> Row:
    raw = _row_dict(all_prs, period_days, sum(reviewer_counts.values()))
    for key in _PER_DEV_AGGREGATED_KEYS:
        values = [m[key] for m in dev_raws.values() if m.get(key)]
        raw[key] = round(median(values), 2) if values else 0.0
    ai_values = [m["ai_percentage"] for m in dev_raws.values()]
    raw["ai_percentage"] = round(sum(ai_values) / len(ai_values), 1) if ai_values else 0.0
    team_health = round(sum(r.health for r in devs) / len(devs)) if devs else 0
    return _to_row("team", raw, team_health)


def _rank(
    raws: dict[str, dict[str, Any]],
    health_fn: Callable[[dict[str, Any], list[dict[str, Any]]], int],
) -> tuple[Row, ...]:
    cohort = list(raws.values())
    rows = [_to_row(name, m, health_fn(m, cohort)) for name, m in raws.items()]
    rows.sort(key=lambda r: r.health, reverse=True)
    return tuple(rows)


def _to_row(name: str, m: dict[str, Any], health: int) -> Row:
    return Row(
        name=name,
        pr_count=int(m.get("pr_count", 0)),
        cycle_time=float(m.get("cycle_time", 0)),
        pickup_time=float(m.get("pickup_time", 0)),
        review_time=float(m.get("review_time", 0)),
        pr_size=float(m.get("pr_size", 0)),
        avg_lines_per_pr=float(m.get("avg_lines_per_pr", 0)),
        prs_per_week=float(m.get("prs_per_week", 0)),
        reviews_given=int(m.get("reviews_given", 0)),
        ai_percentage=float(m.get("ai_percentage", 0)),
        health=health,
        band=_band(health),
    )


def _build_summary(
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


__all__ = ["Band", "MetricsSnapshot", "Row", "Summary"]

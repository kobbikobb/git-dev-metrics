from collections.abc import Callable
from typing import Any

from ..models import PullRequest
from ._dev_repo_metrics import compute_metrics_dict
from ._rows import Band, Row
from .calculator import median

_PER_DEV_AGGREGATED_KEYS = (
    "cycle_time",
    "pickup_time",
    "review_time",
    "pr_size",
    "avg_lines_per_pr",
    "prs_per_week",
)


def band_from_health(health: int) -> Band:
    if health >= 80:
        return "good"
    if health >= 60:
        return "ok"
    return "bad"


def dict_to_row(name: str, m: dict[str, Any], health: int) -> Row:
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
        band=band_from_health(health),
    )


def rank_rows(
    raws: dict[str, dict[str, Any]],
    health_fn: Callable[[dict[str, Any], list[dict[str, Any]]], int],
) -> tuple[Row, ...]:
    cohort = list(raws.values())
    rows = [dict_to_row(name, m, health_fn(m, cohort)) for name, m in raws.items()]
    rows.sort(key=lambda r: r.health, reverse=True)
    return tuple(rows)


def compute_team_row(
    all_prs: list[PullRequest],
    days: int,
    dev_raws: dict[str, dict[str, Any]],
    devs: tuple[Row, ...],
    reviewer_counts: dict[str, int],
) -> Row:
    raw = compute_metrics_dict(all_prs, days, sum(reviewer_counts.values()))
    for key in _PER_DEV_AGGREGATED_KEYS:
        values = [m[key] for m in dev_raws.values() if m.get(key)]
        raw[key] = round(median(values), 2) if values else 0.0
    ai_values = [m["ai_percentage"] for m in dev_raws.values()]
    raw["ai_percentage"] = round(sum(ai_values) / len(ai_values), 1) if ai_values else 0.0
    team_health = round(sum(r.health for r in devs) / len(devs)) if devs else 0
    return dict_to_row("team", raw, team_health)

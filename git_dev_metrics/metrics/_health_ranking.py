from collections.abc import Callable

from ..models import PullRequest
from ._dev_repo_metrics import compute_raw
from ._rows import Band, RawMetrics, Row
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

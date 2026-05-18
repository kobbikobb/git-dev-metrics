from collections.abc import Callable

from ._raw_metrics import RawMetrics
from ._rows import Band, Row


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

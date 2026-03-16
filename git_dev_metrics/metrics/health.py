from typing import Any

BENCHMARKS: dict[str, dict[str, int]] = {
    "cycle_time": {"excellent": 24, "good": 48, "ok": 96, "cap": 168},  # hours
    "pr_size": {"excellent": 200, "good": 500, "ok": 1000, "cap": 10000},  # lines
    "pickup_time": {"excellent": 4, "good": 12, "ok": 48},  # hours
    "prs_per_week": {"excellent": 4, "good": 3, "ok": 2, "bad": 1},  # count
}

LOG_SCALE_DEFAULT_CAP = 2000


def _log_scale(value: float, cap: float) -> float:
    """Apply log scaling to handle outliers."""
    import math

    if value <= 0:
        return 0
    return min(math.log1p(value) / math.log1p(cap) * cap, cap)


def _get_thresholds(metric: str) -> dict[str, int | float]:
    """Get thresholds for a metric."""
    return BENCHMARKS.get(metric, {})  # type: ignore[return-value]


def _calc_prs_per_week_penalty(current: float) -> int:
    """Calculate penalty for prs_per_week (higher is better)."""
    thresholds = BENCHMARKS["prs_per_week"]
    if current >= thresholds["excellent"]:
        return 0
    if current >= thresholds["good"]:
        return 10
    if current >= thresholds["ok"]:
        return 20
    if current >= thresholds["bad"]:
        return 30
    return 35


def _calc_time_penalty(current: float, thresholds: dict[str, float]) -> int:
    """Calculate penalty for time-based metrics."""
    if current <= thresholds.get("excellent", 0):
        return 0
    if current <= thresholds.get("good", 0):
        return 10
    if current <= thresholds.get("ok", 0):
        return 20
    return 35


def calc_benchmark_penalty(current: float, metric: str, use_log: bool = False) -> int:
    """Calculate penalty based on industry benchmarks."""
    if metric not in BENCHMARKS or current <= 0:
        return 0

    bench = _get_thresholds(metric)
    cap = bench.get("cap", None)
    ok_threshold = bench.get("ok", None)

    if cap and current > cap:
        current = cap

    if use_log and ok_threshold and current > ok_threshold:
        current = _log_scale(current, cap or LOG_SCALE_DEFAULT_CAP)

    if metric == "prs_per_week":
        return _calc_prs_per_week_penalty(current)

    if metric == "pickup_time":
        return _calc_time_penalty(current, bench)

    return _calc_time_penalty(current, bench)


def format_health(score: int) -> str:
    """Format health score for display."""
    return str(score)


def get_health_color(score: int) -> str:
    """Return color for health score."""
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def calculate_health_score(
    metrics: dict[str, Any], all_metrics: list[dict[str, Any]] | None = None
) -> int:
    """Calculate health score (0-100) based on industry benchmarks.

    Uses DORA/GitHub engineering benchmarks:
    - cycle_time: ≤24h excellent, ≤48h good, ≤96h ok, >96h penalty (capped at 168h)
    - pr_size: ≤200 excellent, ≤500 good, ≤1000 ok, >1000 penalty (log scaled)
    - pickup_time: ≤4h excellent, ≤12h good, ≤48h ok, >48h penalty
    - prs_per_week: 4+ excellent, <4 penalty
    - reviews_given: +10 if ≥2× PRs, +5 if ≥1× PRs, -15 if <50% of PRs

    Relative bonuses (if all_metrics provided):
    - +10 for highest prs_per_week
    - +10 for most reviews_given
    - +10 for lowest cycle_time (fastest)
    """
    pr_count = metrics.get("pr_count", 0)
    if pr_count == 0:
        return 0

    score = 100

    score -= calc_benchmark_penalty(metrics.get("cycle_time", 0), "cycle_time")
    score -= calc_benchmark_penalty(metrics.get("pr_size", 0), "pr_size", use_log=True)
    score -= calc_benchmark_penalty(metrics.get("pickup_time", 0), "pickup_time")
    score -= calc_benchmark_penalty(metrics.get("prs_per_week", 0), "prs_per_week")

    reviews_given = metrics.get("reviews_given", 0)
    if reviews_given >= pr_count * 2:
        score += 10
    elif reviews_given >= pr_count:
        score += 5

    if reviews_given < pr_count * 0.5:
        score -= 15

    if all_metrics:
        score = _apply_relative_bonuses(metrics, all_metrics, score)

    return max(0, min(100, score))


def _apply_relative_bonuses(
    metrics: dict[str, Any], all_metrics: list[dict[str, Any]], score: int
) -> int:
    """Apply relative bonuses based on group performance."""
    prs_per_week = metrics.get("prs_per_week", 0)
    reviews_given = metrics.get("reviews_given", 0)
    cycle_time = metrics.get("cycle_time", 0)

    max_prs_per_week = max((m.get("prs_per_week", 0) for m in all_metrics), default=0)
    max_reviews_given = max((m.get("reviews_given", 0) for m in all_metrics), default=0)
    min_cycle_time = min(
        (m.get("cycle_time", float("inf")) for m in all_metrics if m.get("cycle_time", 0) > 0),
        default=0,
    )

    if prs_per_week > 0 and prs_per_week >= max_prs_per_week:
        score += 10
    if reviews_given > 0 and reviews_given >= max_reviews_given:
        score += 10
    if cycle_time > 0 and min_cycle_time > 0 and cycle_time <= min_cycle_time:
        score += 10

    return score

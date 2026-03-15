from typing import Any

BENCHMARKS: dict[str, dict[str, int]] = {
    "cycle_time": {"excellent": 24, "good": 48, "ok": 96, "cap": 168},  # hours
    "pr_size": {"excellent": 200, "good": 500, "ok": 1000, "cap": 10000},  # lines
    "pickup_time": {"excellent": 2, "good": 8, "ok": 24},  # hours
    "prs_per_week": {"excellent": 4, "good": 3, "ok": 2, "bad": 1},  # count
}

MIN_PRS_THRESHOLD = 3  # Minimum PRs for scoring


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

    if cap and current > cap:
        current = cap

    if use_log:
        current = _log_scale(current, cap or bench.get("ok", 2000) * 2)

    if metric == "prs_per_week":
        return _calc_prs_per_week_penalty(current)

    if metric == "pickup_time":
        return _calc_time_penalty(current, bench)

    return _calc_time_penalty(current, bench)


def calculate_health_score(metrics: dict[str, Any], all_metrics: list[dict[str, Any]]) -> int:
    """Calculate health score (0-100) based on industry benchmarks.

    Uses DORA/GitHub engineering benchmarks:
    - cycle_time: ≤24h excellent, ≤48h good, ≤96h ok, >96h penalty (capped at 168h)
    - pr_size: ≤200 excellent, ≤500 good, ≤1000 ok, >1000 penalty (log scaled)
    - pickup_time: ≤2h excellent, ≤8h good, ≤24h ok, >24h penalty
    - prs_per_week: 4+ excellent, <4 penalty
    - reviews_given: +10 if ≥2× PRs, +5 if ≥1× PRs, -15 if <50% of PRs

    Returns None if insufficient data (<3 PRs).
    """
    pr_count = metrics.get("pr_count", 0)
    if pr_count < MIN_PRS_THRESHOLD:
        return -1  # Indicate insufficient data

    if not all_metrics:
        return 100

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

    return max(0, min(100, score))

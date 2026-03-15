from typing import Any

BENCHMARKS = {
    "cycle_time": {"excellent": 4, "good": 24, "ok": 72},  # hours
    "pr_size": {"excellent": 100, "good": 400, "ok": 800},  # lines
    "prs_per_week": {"excellent": 5, "good": 3, "ok": 2},  # count
}


def calc_benchmark_penalty(current: float, metric: str) -> int:
    """Calculate penalty based on industry benchmarks."""
    if metric not in BENCHMARKS or current <= 0:
        return 0

    bench = BENCHMARKS[metric]

    if metric == "prs_per_week":
        if current >= bench["excellent"]:
            return 0
        if current >= bench["good"]:
            return 10
        if current >= bench["ok"]:
            return 20
        return 35
    else:
        if current <= bench["excellent"]:
            return 0
        if current <= bench["good"]:
            return 10
        if current <= bench["ok"]:
            return 20
        return 35


def calculate_health_score(metrics: dict[str, Any], all_metrics: list[dict[str, Any]]) -> int:
    """Calculate health score (0-100) based on industry benchmarks.

    Uses DORA/GitHub engineering benchmarks:
    - cycle_time: <4h excellent, <24h good, <72h ok, >72h penalty
    - pr_size: <100 excellent, <400 good, <800 ok, >800 penalty
    - prs_per_week: 5+ excellent, 3-4 good, 2 ok, 1 bad
    - reviews_given: -15 if less than 50% of PRs created
    """
    if not all_metrics:
        return 100

    score = 100

    score -= calc_benchmark_penalty(metrics.get("cycle_time", 0), "cycle_time")
    score -= calc_benchmark_penalty(metrics.get("pr_size", 0), "pr_size")
    score -= calc_benchmark_penalty(metrics.get("prs_per_week", 0), "prs_per_week")

    if metrics.get("reviews_given", 0) < metrics.get("pr_count", 0) * 0.5:
        score -= 15

    return max(0, score)

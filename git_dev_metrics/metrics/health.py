from ._raw_metrics import RawMetrics

TEAM_WEIGHTS = {
    "throughput": 0.25,
    "speed": 0.20,
    "pickup": 0.20,
    "citizenship": 0.35,
}

DEV_WEIGHTS = {
    "throughput": 0.25,
    "speed": 0.30,
    "citizenship": 0.45,
}

THROUGHPUT_GOOD = 6.0
THROUGHPUT_ELITE = 60.0

CYCLE_BANDS = (4, 24, 48, 96)
PICKUP_BANDS = (2, 8, 24, 48)


def _throughput_score(prs_per_week: float) -> float:
    if prs_per_week <= 0:
        return 0.0
    if prs_per_week >= THROUGHPUT_ELITE:
        return 100.0
    if prs_per_week >= THROUGHPUT_GOOD:
        return 80.0 + (prs_per_week - THROUGHPUT_GOOD) / (THROUGHPUT_ELITE - THROUGHPUT_GOOD) * 20
    return prs_per_week / THROUGHPUT_GOOD * 80


def _time_score(value: float, bands: tuple[int, int, int, int]) -> float:
    if value <= 0:
        return 100.0
    excellent, good, ok, bad = bands
    if value <= excellent:
        return 100.0
    if value <= good:
        return 80.0
    if value <= ok:
        return 60.0
    if value <= bad:
        return 40.0
    return 20.0


def _citizenship_score(
    reviews_given: int,
    pr_count: int,
    all_metrics: list[RawMetrics] | None = None,
) -> float:
    """50% ratio + 50% absolute. Absolute scaled vs team max so prolific authors
    aren't penalized for not maintaining 2x review ratio at high PR volume."""
    if pr_count == 0:
        return 0.0

    ratio = reviews_given / pr_count
    ratio_score = min(100.0, ratio * 50)

    if all_metrics:
        max_reviews = max((m.reviews_given for m in all_metrics), default=0)
        absolute_score = (reviews_given / max_reviews * 100) if max_reviews > 0 else 0.0
    else:
        absolute_score = min(100.0, reviews_given / 100 * 100)

    return 0.5 * ratio_score + 0.5 * absolute_score


def calculate_health_score(metrics: RawMetrics, all_metrics: list[RawMetrics] | None = None) -> int:
    """Team/repo composite 0-100. Includes pickup time (team responsiveness)."""
    pr_count = metrics.pr_count
    if pr_count == 0:
        return 0

    components = {
        "throughput": _throughput_score(metrics.prs_per_week),
        "speed": _time_score(metrics.cycle_time, CYCLE_BANDS),
        "pickup": _time_score(metrics.pickup_time, PICKUP_BANDS),
        "citizenship": _citizenship_score(metrics.reviews_given, pr_count, all_metrics),
    }

    score = sum(TEAM_WEIGHTS[k] * v for k, v in components.items())
    return round(max(0.0, min(100.0, score)))


def calculate_dev_health_score(
    metrics: RawMetrics, all_metrics: list[RawMetrics] | None = None
) -> int:
    """Per-developer composite 0-100. Excludes pickup time (reviewer behavior, not author)."""
    pr_count = metrics.pr_count
    if pr_count == 0:
        return 0

    components = {
        "throughput": _throughput_score(metrics.prs_per_week),
        "speed": _time_score(metrics.cycle_time, CYCLE_BANDS),
        "citizenship": _citizenship_score(metrics.reviews_given, pr_count, all_metrics),
    }

    score = sum(DEV_WEIGHTS[k] * v for k, v in components.items())
    return round(max(0.0, min(100.0, score)))


def format_health(score: int) -> str:
    return str(score)


def get_health_color(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"

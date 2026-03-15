from collections import defaultdict
from collections.abc import Callable
from datetime import datetime

from ..models import OpenPullRequest, PullRequest


def _to_datetime(value: str | datetime | None) -> datetime | None:
    """Convert string or datetime to datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def median(values: list[float | int]) -> float:
    """Return median of a list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    return sorted_values[n // 2]


def calculate_cycle_time(prs: list[PullRequest]) -> float:
    """Calculate median time from first commit/PR creation to merge (in hours)."""
    if not prs:
        return 0.0

    cycle_times = []
    for pr in prs:
        created = _to_datetime(pr["created_at"])
        first_commit = _to_datetime(pr.get("first_commit_at"))
        merged = _to_datetime(pr["merged_at"])

        if created is None or merged is None:
            continue

        start_time = created
        if first_commit is not None and first_commit < created:
            start_time = first_commit

        hours = (merged - start_time).total_seconds() / 3600
        cycle_times.append(hours)

    return round(median(cycle_times), 2)


def calculate_pr_size(prs: list[PullRequest]) -> int:
    """Calculate median PR size (lines changed)."""
    if not prs:
        return 0

    pr_sizes = [float(pr.get("additions", 0) + pr.get("deletions", 0)) for pr in prs]
    return round(median(pr_sizes))


def calculate_throughput(prs: list[PullRequest]) -> int:
    """Calculate number of merged PRs."""
    return len(prs)


def calculate_pickup_time(prs: list[PullRequest], reviews: dict) -> float:
    """Calculate median time from PR creation to first approval (in hours)."""
    if not prs:
        return 0.0

    pickup_times = []
    for pr in prs:
        pr_number = pr["number"]
        pr_reviews = reviews.get(pr_number, [])
        created = _to_datetime(pr["created_at"])
        if created is None:
            continue

        first_approval = None
        for review in pr_reviews:
            if review.get("state") == "APPROVED":
                first_approval = _to_datetime(review.get("submitted_at"))
                break

        if first_approval:
            hours = (first_approval - created).total_seconds() / 3600
            pickup_times.append(hours)

    if not pickup_times:
        return 0.0
    return round(median(pickup_times), 2)


def calculate_review_time(prs: list[PullRequest], reviews: dict) -> float:
    """Calculate median time from first approval to merge (in hours)."""
    if not prs:
        return 0.0

    review_times = []
    for pr in prs:
        pr_number = pr["number"]
        pr_reviews = reviews.get(pr_number, [])
        merged = _to_datetime(pr["merged_at"])

        first_approval = None
        for review in pr_reviews:
            if review.get("state") == "APPROVED":
                first_approval = _to_datetime(review.get("submitted_at"))
                break

        if merged and first_approval:
            hours = (merged - first_approval).total_seconds() / 3600
            review_times.append(hours)

    if not review_times:
        return 0.0
    return round(median(review_times), 2)


def calculate_prs_per_week(prs: list[PullRequest], period_days: int) -> float:
    """Calculate average PRs per week."""
    if not prs:
        return 0.0
    weeks = max(period_days / 7, 1)
    return round(len(prs) / weeks, 2)


def group_prs_by_devs(prs: list[PullRequest]) -> dict[str, list[PullRequest]]:
    """Group PRs by developer."""
    devs = defaultdict(list)
    for pr in prs:
        dev = pr["user"]["login"]
        devs[dev].append(pr)
    return devs


def calculate_reviews_given(reviews: dict, devs: dict[str, list[PullRequest]]) -> dict[str, int]:
    """Calculate number of PRs reviewed by each developer."""
    reviewer_counts: dict[str, int] = {dev: 0 for dev in devs}

    for _pr_number, pr_reviews in reviews.items():
        for review in pr_reviews:
            reviewer = review.get("user", {}).get("login")
            if reviewer:
                if reviewer in reviewer_counts:
                    reviewer_counts[reviewer] += 1
                elif reviewer not in devs:
                    reviewer_counts[reviewer] = 1

    return reviewer_counts


STALE_PR_THRESHOLD_HOURS = 24 * 7  # 7 days


def _calculate_age_hours(
    created_at: str | datetime, clock: Callable[[], datetime] | None = None
) -> float:
    """Calculate age in hours from created_at to now."""
    from datetime import UTC, datetime

    now = clock() if clock else datetime.now(UTC)
    parsed: datetime | None = (
        _to_datetime(created_at) if isinstance(created_at, str) else created_at
    )
    if parsed is None:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return (now - parsed).total_seconds() / 3600


def _is_stale_pr(
    pr: OpenPullRequest, repo: str, clock: Callable[[], datetime] | None = None
) -> dict | None:
    """Check if PR is stale and return data if so."""
    created = pr.get("created_at")
    if created is None:
        return None

    age_hours = _calculate_age_hours(created, clock)
    if age_hours > STALE_PR_THRESHOLD_HOURS:
        return {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "author": pr.get("user", {}).get("login"),
            "repo": repo,
            "age_hours": round(age_hours, 1),
            "url": f"https://github.com/{repo}/pull/{pr.get('number')}",
        }
    return None


def get_stale_prs(
    prs: list[OpenPullRequest], repo: str = "", clock: Callable[[], datetime] | None = None
) -> list[dict]:
    """Return list of stale PRs (> 7 days old), sorted by age (oldest first)."""
    stale = [p for p in (_is_stale_pr(pr, repo, clock) for pr in prs) if p]
    stale.sort(key=lambda x: x["age_hours"], reverse=True)
    return stale


def _percentile(values: list[float], p: float) -> float:
    """Return the p-th percentile of values (0-100)."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = int(len(sorted_values) * p / 100)
    idx = min(idx, len(sorted_values) - 1)
    return sorted_values[idx]


def calculate_health_score(metrics: dict, all_metrics: list[dict]) -> int:
    """Calculate health score (0-100) based on percentile rankings.

    Returns 100 for healthy (at or below 50th percentile), lower for outliers.
    """
    if not all_metrics:
        return 100

    score = 100

    lower_is_worse = ["cycle_time", "pr_size"]
    higher_is_better = ["pr_count", "reviews_given"]

    for key in lower_is_worse + higher_is_better:
        raw_values = [m.get(key, 0) for m in all_metrics if m.get(key)]
        values: list[float] = [float(v) for v in raw_values if v is not None and float(v) > 0]
        if not values:
            continue

        current = float(metrics.get(key, 0) or 0)

        p50 = _percentile(values, 50)
        p75 = _percentile(values, 75)
        p90 = _percentile(values, 90)
        p10 = _percentile(values, 10)
        p25 = _percentile(values, 25)

        if key in lower_is_worse:
            if current >= p90:
                score -= 25
            elif current >= p75:
                score -= 15
            elif current > p50 and p50 > 0:
                score -= 5
        else:
            if current > 0 and current <= p10:
                score -= 25
            elif current <= p25:
                score -= 15
            elif current <= p50:
                score -= 5

    return max(0, score)

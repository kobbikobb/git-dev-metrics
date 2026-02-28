from collections import defaultdict
from datetime import datetime

from ..models import PullRequest


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
    """Calculate median time from PR creation to merge (in hours)."""
    if not prs:
        return 0.0

    cycle_times = []
    for pr in prs:
        created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
        hours = (merged - created).total_seconds() / 3600
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
        created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))

        first_approval = None
        for review in pr_reviews:
            if review.get("state") == "APPROVED":
                first_approval = datetime.fromisoformat(
                    review["submitted_at"].replace("Z", "+00:00")
                )
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
        merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))

        first_approval = None
        for review in pr_reviews:
            if review.get("state") == "APPROVED":
                first_approval = datetime.fromisoformat(
                    review["submitted_at"].replace("Z", "+00:00")
                )
                break

        if first_approval:
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

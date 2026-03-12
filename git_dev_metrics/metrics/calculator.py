from collections import defaultdict
from datetime import UTC, datetime

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


# Bottleneck detection thresholds (in hours)
STALE_PR_THRESHOLD_HOURS = 24 * 7  # 7 days
REVIEW_WAIT_THRESHOLD_HOURS = 48  # 2 days
OVERWHELMED_REVIEWER_COUNT = 5


def calculate_pr_aging(prs: list[OpenPullRequest]) -> dict:
    """Calculate PR aging metrics for open PRs."""
    if not prs:
        return {
            "open_count": 0,
            "stale_count": 0,
            "avg_age_hours": 0.0,
            "oldest_pr_age_hours": 0.0,
        }

    now = datetime.now(UTC)
    ages_hours = []
    stale_count = 0

    for pr in prs:
        created = _to_datetime(pr.get("created_at"))
        if created is None:
            continue

        # Handle naive datetimes
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)

        age_hours = (now - created).total_seconds() / 3600
        ages_hours.append(age_hours)

        if age_hours > STALE_PR_THRESHOLD_HOURS:
            stale_count += 1

    if not ages_hours:
        return {
            "open_count": len(prs),
            "stale_count": 0,
            "avg_age_hours": 0.0,
            "oldest_pr_age_hours": 0.0,
        }

    return {
        "open_count": len(prs),
        "stale_count": stale_count,
        "avg_age_hours": round(sum(ages_hours) / len(ages_hours), 2),
        "oldest_pr_age_hours": round(max(ages_hours), 2),
    }


def identify_bottlenecks(prs: list[OpenPullRequest]) -> dict:
    """Identify PRs and reviewers that are bottlenecks."""
    now = datetime.now(UTC)

    stale_prs = []
    waiting_for_review = []
    reviewer_load: dict[str, int] = defaultdict(int)

    for pr in prs:
        created = _to_datetime(pr.get("created_at"))
        if created is None:
            continue

        # Handle naive datetimes
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)

        age_hours = (now - created).total_seconds() / 3600
        pr_number = pr.get("number")
        title = pr.get("title", "")
        author = pr.get("user", {}).get("login", "unknown")

        # Check if stale
        if age_hours > STALE_PR_THRESHOLD_HOURS:
            stale_prs.append(
                {
                    "number": pr_number,
                    "title": title,
                    "author": author,
                    "age_hours": round(age_hours, 2),
                }
            )

        # Check if waiting for review
        requested_reviewers = pr.get("requested_reviewers", [])
        if age_hours > REVIEW_WAIT_THRESHOLD_HOURS and not requested_reviewers:
            waiting_for_review.append(
                {
                    "number": pr_number,
                    "title": title,
                    "author": author,
                    "waiting_hours": round(age_hours, 2),
                }
            )

        # Count reviewer load
        for reviewer in requested_reviewers:
            reviewer_login = reviewer.get("login")
            if reviewer_login:
                reviewer_load[reviewer_login] += 1

    # Find overwhelmed reviewers
    overwhelmed_reviewers = [
        {"reviewer": reviewer, "pending_count": count}
        for reviewer, count in reviewer_load.items()
        if count >= OVERWHELMED_REVIEWER_COUNT
    ]
    overwhelmed_reviewers.sort(key=lambda x: x["pending_count"], reverse=True)

    # Sort by age (oldest first) before limiting
    stale_prs.sort(key=lambda x: x["age_hours"], reverse=True)
    waiting_for_review.sort(key=lambda x: x["waiting_hours"], reverse=True)

    return {
        "stale_prs": stale_prs[:10],  # Top 10 oldest stale PRs
        "waiting_for_review": waiting_for_review[:10],
        "overwhelmed_reviewers": overwhelmed_reviewers[:10],
    }

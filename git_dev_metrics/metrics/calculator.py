from collections import defaultdict
from datetime import datetime

from ..constants import is_bot_login
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


def _pr_start_time(pr: PullRequest) -> datetime | None:
    created = pr["created_at"]
    if created is None:
        return None
    first_commit = pr.get("first_commit_at")
    start = first_commit if first_commit is not None and first_commit < created else created
    ready_for_review = pr.get("ready_for_review_at")
    if ready_for_review is not None and ready_for_review > start:
        start = ready_for_review
    return start


def calculate_cycle_time(prs: list[PullRequest]) -> float:
    """Median hours from first commit/ready-for-review to merge for approved PRs.

    Restricted to PRs that received at least one approval so the team-level
    invariant pickup <= cycle holds. PRs merged without review (auto-merge,
    owner override) are excluded.
    """
    if not prs:
        return 0.0

    cycle_times = []
    for pr in prs:
        merged = pr["merged_at"]
        start_time = _pr_start_time(pr)
        if start_time is None or merged is None:
            continue
        if _first_approval_at(pr) is None:
            continue

        hours = (merged - start_time).total_seconds() / 3600
        cycle_times.append(hours)

    if not cycle_times:
        return 0.0
    return round(median(cycle_times), 2)


def calculate_pr_size(prs: list[PullRequest]) -> int:
    """Calculate median PR size (lines changed)."""
    if not prs:
        return 0

    pr_sizes = [float(abs(pr.get("additions", 0)) + abs(pr.get("deletions", 0))) for pr in prs]
    return round(median(pr_sizes))


def calculate_avg_lines_per_pr(prs: list[PullRequest]) -> float:
    """Calculate average lines changed per PR."""
    if not prs:
        return 0.0
    total = sum(abs(pr.get("additions", 0)) + abs(pr.get("deletions", 0)) for pr in prs)
    return round(total / len(prs), 1)


def calculate_throughput(prs: list[PullRequest]) -> int:
    """Calculate number of merged PRs."""
    return len(prs)


def _first_approval_at(pr: PullRequest) -> datetime | None:
    for review in pr.get("reviews", []):
        if review.get("state") == "APPROVED":
            return review.get("submitted_at")
    return None


def calculate_pickup_time(prs: list[PullRequest]) -> float:
    """Median hours from PR ready-for-review to first approval, excluding draft time."""
    if not prs:
        return 0.0

    pickup_times = []
    for pr in prs:
        start_time = _pr_start_time(pr)
        first_approval = _first_approval_at(pr)
        if start_time is None or first_approval is None:
            continue
        pickup_times.append((first_approval - start_time).total_seconds() / 3600)

    if not pickup_times:
        return 0.0
    return round(median(pickup_times), 2)


def calculate_review_time(prs: list[PullRequest]) -> float:
    """Calculate median time from first approval to merge (in hours)."""
    if not prs:
        return 0.0

    review_times = []
    for pr in prs:
        merged = pr["merged_at"]
        first_approval = _first_approval_at(pr)
        if merged and first_approval:
            review_times.append((merged - first_approval).total_seconds() / 3600)

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
    """Group PRs by developer, excluding known bots."""
    devs = defaultdict(list)
    for pr in prs:
        dev = pr["user"]["login"]
        if not is_bot_login(dev):
            devs[dev].append(pr)
    return devs


def calculate_reviews_given(prs: list[PullRequest]) -> dict[str, int]:
    """Count PRs reviewed by each developer. One per PR, excludes self-reviews and bots."""
    reviewer_counts: dict[str, int] = {}

    for pr in prs:
        author = pr["user"]["login"]
        counted: set[str] = set()
        for review in pr.get("reviews", []):
            reviewer = review.get("user", {}).get("login")
            if not reviewer or is_bot_login(reviewer):
                continue
            if reviewer == author or reviewer in counted:
                continue
            counted.add(reviewer)
            reviewer_counts[reviewer] = reviewer_counts.get(reviewer, 0) + 1

    return reviewer_counts

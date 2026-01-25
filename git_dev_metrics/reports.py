from datetime import datetime, timedelta
from typing import List, Dict, Any, TypedDict
from .queries import fetch_pull_requests, fetch_repositories


def parse_time_period(event_period: str) -> datetime:
    """Parse time period string and return the start date."""
    period_map = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
    }

    delta = period_map.get(event_period, timedelta(days=30))
    return datetime.now() - delta


class PullRequest(TypedDict):
    number: int
    state: str
    created_at: str
    closed_at: str
    merged_at: str
    additions: int
    deletions: int
    changed_files: int


def calculate_cycle_time(prs: List[Dict[Any, Any]]) -> float:
    """Calculate average time from PR creation to merge (in days)."""
    if not prs:
        return 0.0

    total_hours = 0
    for pr in prs:
        created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
        total_hours += (merged - created).total_seconds() / 3600

    return round(total_hours / len(prs) / 24, 2)


def calculate_pr_size(prs: List[Dict[Any, Any]]) -> int:
    """Calculate average PR size (lines changed)."""
    if not prs:
        return 0

    total_changes = sum(pr.get("additions", 0) + pr.get("deletions", 0) for pr in prs)
    return round(total_changes / len(prs))


def calculate_throughput(prs: List[Dict[Any, Any]]) -> int:
    """Calculate number of merged PRs."""
    return len(prs)


def get_pull_request_metrics(
    token: str, org: str, repo: str, event_period: str = "30d"
) -> dict:
    """
    Get development metrics for a repository over a specified time period.
    """
    since = parse_time_period(event_period)
    prs = fetch_pull_requests(token, org, repo, since)

    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "throughput": calculate_throughput(prs),
    }


def get_all_repositories(token: str) -> dict:
    """List all repositories accessible with the given GitHub token."""
    repos = fetch_repositories(token)

    return {
        repo["full_name"]: "Private" if repo["private"] else "Public" for repo in repos
    }

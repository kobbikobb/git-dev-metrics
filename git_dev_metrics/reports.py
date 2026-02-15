from collections import defaultdict
from datetime import datetime

from .date_utils import parse_time_period
from .queries import fetch_pull_requests, fetch_repositories
from .type_definitions import PullRequest


def calculate_cycle_time(prs: list[PullRequest]) -> float:
    """Calculate average time from PR creation to merge (in days)."""
    if not prs:
        return 0.0

    total_hours = 0
    for pr in prs:
        created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
        total_hours += (merged - created).total_seconds() / 3600

    return round(total_hours / len(prs) / 24, 2)


def calculate_pr_size(prs: list[PullRequest]) -> int:
    """Calculate average PR size (lines changed)."""
    if not prs:
        return 0

    total_changes = sum(pr.get("additions", 0) + pr.get("deletions", 0) for pr in prs)
    return round(total_changes / len(prs))


def calculate_throughput(prs: list[PullRequest]) -> int:
    """Calculate number of merged PRs."""
    return len(prs)


def group_prs_by_devs(prs: list[PullRequest]) -> dict[str, list[PullRequest]]:
    """Group PRs by developer."""
    devs = defaultdict(list)
    for pr in prs:
        dev = pr["user"]["login"]
        devs[dev].append(pr)
    return devs


def get_pull_request_metrics(token: str, org: str, repo: str, event_period: str = "30d") -> dict:
    """
    Get development metrics for a repository over a specified time period.
    """
    since = parse_time_period(event_period)
    prs = fetch_pull_requests(token, org, repo, since)

    devs = group_prs_by_devs(prs)

    dev_metrics = {}
    for dev, dev_prs in devs.items():
        dev_metrics[dev] = {
            "cycle_time": calculate_cycle_time(dev_prs),
            "pr_size": calculate_pr_size(dev_prs),
            "throughput": calculate_throughput(dev_prs),
        }

    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "throughput": calculate_throughput(prs),
        "dev_metrics": dev_metrics,
    }


def get_all_repositories(token: str) -> dict:
    """List all repositories accessible with the given GitHub token."""
    repos = fetch_repositories(token)

    return {repo["full_name"]: "Private" if repo["private"] else "Public" for repo in repos}

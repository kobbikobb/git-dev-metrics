from ..github import fetch_pull_requests, fetch_repositories
from ..utils import parse_time_period
from .calculator import (
    calculate_cycle_time,
    calculate_pr_size,
    calculate_throughput,
    group_prs_by_devs,
)


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
    """Get all repositories accessible with the given GitHub token."""
    repos = fetch_repositories(token)

    return {repo["full_name"]: "Private" if repo["private"] else "Public" for repo in repos}

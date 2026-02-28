import re
from datetime import datetime

from ..github import fetch_pull_requests, fetch_repositories, fetch_reviews
from ..utils import parse_time_period
from .calculator import (
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_throughput,
    group_prs_by_devs,
)


def _parse_period_days(event_period: str) -> int:
    """Extract number of days from period string like '30d', '2w', '1m'."""
    match = re.match(r"(\d+)(d|w|m)", event_period)
    if not match:
        return 30
    value, unit = match.groups()
    days = int(value)
    if unit == "w":
        days *= 7
    elif unit == "m":
        days *= 30
    return days


def get_pull_request_metrics(token: str, org: str, repo: str, event_period: str = "30d") -> dict:
    """
    Get development metrics for a repository over a specified time period.
    """
    since = parse_time_period(event_period)
    prs = fetch_pull_requests(token, org, repo, since)

    period_days = _parse_period_days(event_period)

    pr_numbers = [pr["number"] for pr in prs]
    reviews = fetch_reviews(token, org, repo, pr_numbers)

    devs = group_prs_by_devs(prs)

    dev_metrics = {}
    for dev, dev_prs in devs.items():
        dev_metrics[dev] = {
            "cycle_time": calculate_cycle_time(dev_prs),
            "pr_size": calculate_pr_size(dev_prs),
            "pr_count": calculate_throughput(dev_prs),
            "pickup_time": calculate_pickup_time(dev_prs, reviews),
            "review_time": calculate_review_time(dev_prs, reviews),
            "prs_per_week": calculate_prs_per_week(dev_prs, period_days),
        }

    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "pr_count": calculate_throughput(prs),
        "pickup_time": calculate_pickup_time(prs, reviews),
        "review_time": calculate_review_time(prs, reviews),
        "prs_per_week": calculate_prs_per_week(prs, period_days),
        "dev_metrics": dev_metrics,
    }


def get_recent_repositories(token: str) -> dict:
    """Get all repositories accessible with the given GitHub token."""
    repos = fetch_repositories(token)

    recent_repos = [
        r
        for r in repos
        if r["last_pushed"] is not None and r["last_pushed"] >= parse_time_period("d180")
    ]
    recent_repos.sort(key=lambda r: r["last_pushed"] or datetime.min, reverse=True)

    return {repo["full_name"]: "Private" if repo["private"] else "Public" for repo in recent_repos}

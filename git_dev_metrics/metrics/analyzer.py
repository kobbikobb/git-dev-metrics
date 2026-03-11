import re
from datetime import datetime

from ..github import fetch_repo_metrics, fetch_repositories
from ..utils import parse_time_period
from .calculator import (
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_reviews_given,
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
    prs, reviews = fetch_repo_metrics(token, org, repo, since)

    period_days = _parse_period_days(event_period)

    devs = group_prs_by_devs(prs)
    reviews_given = calculate_reviews_given(reviews, devs)

    dev_metrics = {}
    for dev, dev_prs in devs.items():
        dev_metrics[dev] = {
            "cycle_time": calculate_cycle_time(dev_prs),
            "pr_size": calculate_pr_size(dev_prs),
            "pr_count": calculate_throughput(dev_prs),
            "pickup_time": calculate_pickup_time(dev_prs, reviews),
            "review_time": calculate_review_time(dev_prs, reviews),
            "prs_per_week": calculate_prs_per_week(dev_prs, period_days),
            "reviews_given": reviews_given.get(dev, 0),
        }

    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "pr_count": calculate_throughput(prs),
        "pickup_time": calculate_pickup_time(prs, reviews),
        "review_time": calculate_review_time(prs, reviews),
        "prs_per_week": calculate_prs_per_week(prs, period_days),
        "reviews_given": sum(reviews_given.values()),
        "dev_metrics": dev_metrics,
    }


def get_combined_metrics(token: str, selected_repos: list[str], event_period: str = "30d") -> dict:
    """
    Get combined metrics for multiple repositories.

    Returns dict with:
    - repo_metrics: dict mapping repo_name -> repo-level metrics
    - dev_metrics: dict mapping dev_name -> combined dev-level metrics across all repos
    """
    since = parse_time_period(event_period)
    period_days = _parse_period_days(event_period)

    all_prs: list = []
    all_reviews: dict = {}
    repo_metrics: dict = {}

    for full_name in selected_repos:
        org, name = full_name.split("/", 1)
        prs, reviews = fetch_repo_metrics(token, org, name, since)

        all_prs.extend(prs)
        all_reviews.update(reviews)

        devs = group_prs_by_devs(prs)
        reviews_given = calculate_reviews_given(reviews, devs)

        repo_metrics[full_name] = {
            "cycle_time": calculate_cycle_time(prs),
            "pr_size": calculate_pr_size(prs),
            "pr_count": calculate_throughput(prs),
            "pickup_time": calculate_pickup_time(prs, reviews),
            "review_time": calculate_review_time(prs, reviews),
            "prs_per_week": calculate_prs_per_week(prs, period_days),
            "reviews_given": sum(reviews_given.values()),
        }

    all_devs = group_prs_by_devs(all_prs)
    all_reviews_given = calculate_reviews_given(all_reviews, all_devs)

    combined_dev_metrics = {}
    for dev, dev_prs in all_devs.items():
        combined_dev_metrics[dev] = {
            "cycle_time": calculate_cycle_time(dev_prs),
            "pr_size": calculate_pr_size(dev_prs),
            "pr_count": calculate_throughput(dev_prs),
            "pickup_time": calculate_pickup_time(dev_prs, all_reviews),
            "review_time": calculate_review_time(dev_prs, all_reviews),
            "prs_per_week": calculate_prs_per_week(dev_prs, period_days),
            "reviews_given": all_reviews_given.get(dev, 0),
        }

    return {
        "repo_metrics": repo_metrics,
        "dev_metrics": combined_dev_metrics,
    }


def get_recent_repositories(token: str) -> dict:
    """Get all repositories accessible with the given GitHub token."""
    repos = fetch_repositories(token)

    recent_repos = [
        r
        for r in repos
        if r["last_pushed"] is not None and r["last_pushed"] >= parse_time_period("180d")
    ]
    recent_repos.sort(key=lambda r: r["last_pushed"] or datetime.min, reverse=True)

    return {repo["full_name"]: "Private" if repo["private"] else "Public" for repo in recent_repos}

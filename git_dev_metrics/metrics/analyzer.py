import re

from ..github import fetch_repo_metrics
from ..utils import parse_time_period
from .calculator import (
    calculate_ai_percentage,
    calculate_avg_lines_per_pr,
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_reviews_given,
    calculate_throughput,
    group_prs_by_devs,
    median,
)

_PER_DEV_AGGREGATED_KEYS = (
    "cycle_time",
    "pickup_time",
    "review_time",
    "pr_size",
    "avg_lines_per_pr",
    "prs_per_week",
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


def _build_dev_metrics(devs: dict, period_days: int, reviews_given: dict) -> dict:
    """Build dev-level metrics dict."""
    return {
        dev: {
            "cycle_time": calculate_cycle_time(dev_prs),
            "pr_size": calculate_pr_size(dev_prs),
            "avg_lines_per_pr": calculate_avg_lines_per_pr(dev_prs),
            "pr_count": calculate_throughput(dev_prs),
            "pickup_time": calculate_pickup_time(dev_prs),
            "review_time": calculate_review_time(dev_prs),
            "prs_per_week": calculate_prs_per_week(dev_prs, period_days),
            "reviews_given": reviews_given.get(dev, 0),
            "ai_percentage": calculate_ai_percentage(dev_prs),
        }
        for dev, dev_prs in devs.items()
    }


def get_pull_request_metrics(token: str, org: str, repo: str, event_period: str = "30d") -> dict:
    """Get development metrics for a repository over a specified time period."""
    period = parse_time_period(event_period)
    period_days = _parse_period_days(event_period)
    prs = fetch_repo_metrics(token, org, repo, period)

    devs = group_prs_by_devs(prs)
    reviews_given = calculate_reviews_given(prs)
    dev_metrics = _build_dev_metrics(devs, period_days, reviews_given)

    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "avg_lines_per_pr": calculate_avg_lines_per_pr(prs),
        "pr_count": calculate_throughput(prs),
        "pickup_time": calculate_pickup_time(prs),
        "review_time": calculate_review_time(prs),
        "prs_per_week": calculate_prs_per_week(prs, period_days),
        "reviews_given": sum(reviews_given.values()),
        "ai_percentage": calculate_ai_percentage(prs),
        "dev_metrics": dev_metrics,
    }


def _build_metrics(prs: list, period_days: int) -> dict:
    """Build metrics dict for a list of PRs."""
    reviews_given = calculate_reviews_given(prs)
    return {
        "cycle_time": calculate_cycle_time(prs),
        "pr_size": calculate_pr_size(prs),
        "avg_lines_per_pr": calculate_avg_lines_per_pr(prs),
        "pr_count": calculate_throughput(prs),
        "pickup_time": calculate_pickup_time(prs),
        "review_time": calculate_review_time(prs),
        "prs_per_week": calculate_prs_per_week(prs, period_days),
        "reviews_given": sum(reviews_given.values()),
        "ai_percentage": calculate_ai_percentage(prs),
    }


def get_combined_metrics(token: str, selected_repos: list[str], event_period: str = "30d") -> dict:
    """Get combined metrics for multiple repositories."""
    period = parse_time_period(event_period)
    period_days = _parse_period_days(event_period)

    all_prs: list = []
    repo_metrics: dict = {}

    for full_name in selected_repos:
        org, name = full_name.split("/", 1)
        prs = fetch_repo_metrics(token, org, name, period)

        all_prs.extend(prs)
        repo_metrics[full_name] = _build_metrics(prs, period_days)

    all_devs = group_prs_by_devs(all_prs)
    all_reviews_given = calculate_reviews_given(all_prs)
    combined_dev_metrics = _build_dev_metrics(all_devs, period_days, all_reviews_given)
    team_metrics = _build_metrics(all_prs, period_days)
    for key in _PER_DEV_AGGREGATED_KEYS:
        values = [m[key] for m in combined_dev_metrics.values() if m.get(key)]
        team_metrics[key] = round(median(values), 2) if values else 0.0
    ai_values = [m["ai_percentage"] for m in combined_dev_metrics.values()]
    team_metrics["ai_percentage"] = round(sum(ai_values) / len(ai_values), 1) if ai_values else 0.0

    return {
        "repo_metrics": repo_metrics,
        "dev_metrics": combined_dev_metrics,
        "team_metrics": team_metrics,
        "reviewer_counts": all_reviews_given,
    }

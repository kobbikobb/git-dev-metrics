from datetime import datetime

from ..models import OpenPullRequest, PullRequest, Repository, Review
from ..utils import TimePeriod
from .graphql_client import execute_paginated_query, get_client
from .graphql_queries import (
    OPEN_PRS_QUERY,
    ORG_REPOSITORIES_QUERY,
    REPO_METRICS_QUERY,
    REPOSITORIES_QUERY,
    SEARCH_MERGED_PRS_QUERY,
)

PAGE_SIZE = 50


def _build_merged_prs_query(org: str, repo: str, period: TimePeriod) -> str:
    """Build GitHub search query for PRs merged within a TimePeriod."""
    since = period.since.strftime("%Y-%m-%d")
    until = period.until.strftime("%Y-%m-%d")
    return f"repo:{org}/{repo} is:pr merged:{since}..{until}"


def _author_login(author: dict | None) -> str:
    """Extract login from author dict, default to 'unknown' if missing."""
    return (author or {}).get("login") or "unknown"


def _parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse ISO datetime string to datetime object."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _map_repository(repo: dict) -> Repository:
    """Map GraphQL repository response to internal model."""
    return {
        "full_name": repo.get("nameWithOwner"),  # type: ignore[return-value]
        "private": repo.get("isPrivate", False),
        "last_pushed": _parse_datetime(repo.get("pushedAt")),
    }


def _map_pull_request(pr: dict) -> PullRequest:
    """Map GraphQL PR response to internal model."""
    commits = pr.get("commits", {}).get("nodes", [])
    first_commit_date = None
    if commits:
        commit_data = commits[-1].get("commit", {})
        committed_at = commit_data.get("committedDate")
        first_commit_date = _parse_datetime(committed_at)

    commit_messages = [msg for c in commits if (msg := (c.get("commit") or {}).get("message"))]

    return {  # type: ignore[return-value]
        "number": pr.get("number"),
        "title": pr.get("title"),
        "created_at": _parse_datetime(pr.get("createdAt")),
        "merged_at": _parse_datetime(pr.get("mergedAt")),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "changed_files": pr.get("changedFiles", 0),
        "user": {"login": _author_login(pr.get("author"))},
        "first_commit_at": first_commit_date,
        "body": pr.get("body"),
        "labels": [label.get("name") for label in pr.get("labels", {}).get("nodes", [])],
        "commit_messages": commit_messages,
        "reviews": [],
    }


def _map_review(review: dict) -> Review:
    """Map GraphQL review response to internal model."""
    return {  # type: ignore[return-value]
        "user": {"login": _author_login(review.get("author"))},
        "state": review.get("state"),
        "submitted_at": _parse_datetime(review.get("submittedAt")),
    }


def fetch_repositories(token: str) -> list[Repository]:
    """Fetch all repositories accessible with the given token."""
    client = get_client(token)
    repos = execute_paginated_query(
        client, REPOSITORIES_QUERY, {"first": PAGE_SIZE}, "viewer.repositories"
    )

    return [_map_repository(repo) for repo in repos if repo.get("nameWithOwner")]


def fetch_org_repositories(token: str, org: str) -> list[Repository]:
    """Fetch all repositories for a specific organization."""
    client = get_client(token)
    repos = execute_paginated_query(
        client,
        ORG_REPOSITORIES_QUERY,
        {"login": org, "first": PAGE_SIZE},
        "organization.repositories",
    )

    return [_map_repository(repo) for repo in repos if repo.get("nameWithOwner")]


def fetch_pull_requests(token: str, org: str, repo: str, period: TimePeriod) -> list[PullRequest]:
    """Fetch merged pull requests within a TimePeriod using search API."""
    client = get_client(token)
    search_query = _build_merged_prs_query(org, repo, period)
    prs = execute_paginated_query(
        client,
        SEARCH_MERGED_PRS_QUERY,
        {"query": search_query, "first": PAGE_SIZE},
        "search",
        repo_id=f"{org}/{repo}",
    )

    return [_map_pull_request(pr) for pr in prs if pr.get("mergedAt")]


def fetch_reviews(
    token: str, org: str, repo: str, pr_numbers: list[int], period: TimePeriod
) -> dict[int, list[Review]]:
    """Fetch all reviews for the given PRs."""
    if not pr_numbers:
        return {}

    client = get_client(token)
    prs = execute_paginated_query(
        client,
        REPO_METRICS_QUERY,
        {"owner": org, "name": repo, "first": PAGE_SIZE},
        "repository.pullRequests",
    )

    reviews_by_pr: dict[int, list[Review]] = {pr_num: [] for pr_num in pr_numbers}

    for pr in prs:
        pr_number = pr.get("number")
        if pr_number not in pr_numbers:
            continue

        reviews = pr.get("reviews", {}).get("nodes", [])
        reviews_by_pr[pr_number] = [_map_review(r) for r in reviews]

    return reviews_by_pr


def _filter_and_map_pr(prs: list[dict], period: TimePeriod) -> list[PullRequest]:
    """Filter PRs by TimePeriod and attach reviews to each PR."""
    mapped_prs: list[PullRequest] = []

    for pr in prs:
        mapped = _map_pull_request(pr)
        merged_at = mapped["merged_at"]
        if merged_at is None or merged_at < period.since or merged_at >= period.until:  # type: ignore[reportOperatorIssue]
            continue

        review_nodes = pr.get("reviews", {}).get("nodes", [])
        mapped["reviews"] = [_map_review(r) for r in review_nodes]
        mapped_prs.append(mapped)

    return mapped_prs


def fetch_repo_metrics(token: str, org: str, repo: str, period: TimePeriod) -> list[PullRequest]:
    """Fetch PRs (with attached reviews) in a single query using search API."""
    client = get_client(token)
    search_query = _build_merged_prs_query(org, repo, period)
    prs = execute_paginated_query(
        client,
        SEARCH_MERGED_PRS_QUERY,
        {"query": search_query, "first": PAGE_SIZE},
        "search",
        repo_id=f"{org}/{repo}",
    )

    return _filter_and_map_pr(prs, period)


def fetch_open_prs(token: str, org: str, repo: str, quiet: bool = False) -> list[OpenPullRequest]:
    """Fetch open pull requests for a repository."""
    client = get_client(token)
    prs = execute_paginated_query(
        client,
        OPEN_PRS_QUERY,
        {"owner": org, "name": repo, "first": PAGE_SIZE},
        "repository.pullRequests",
        repo_id=f"{org}/{repo}",
        quiet=quiet,
    )

    result: list[OpenPullRequest] = []
    for pr in prs:
        number = pr.get("number")
        title = pr.get("title")
        if number is None or title is None:
            continue
        reviews = pr.get("reviews", {}).get("nodes", [])
        is_approved = any(r.get("state") == "APPROVED" for r in reviews)
        result.append(
            {
                "number": number,
                "title": title,
                "created_at": pr.get("createdAt"),
                "merged_at": None,
                "user": {"login": _author_login(pr.get("author"))},
                "is_draft": pr.get("isDraft", False),
                "is_approved": is_approved,
            }
        )
    return result

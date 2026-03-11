from datetime import datetime

from ..models import PullRequest, Repository, Review
from .graphql_client import execute_paginated_query, get_client
from .graphql_queries import (
    REPO_METRICS_QUERY,
    REPOSITORIES_QUERY,
)

PAGE_SIZE = 100


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
    return {  # type: ignore[return-value]
        "number": pr.get("number"),
        "title": pr.get("title"),
        "created_at": _parse_datetime(pr.get("createdAt")),
        "merged_at": _parse_datetime(pr.get("mergedAt")),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "changed_files": pr.get("changedFiles", 0),
        "user": {"login": _author_login(pr.get("author"))},
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


def fetch_pull_requests(token: str, org: str, repo: str, since: datetime) -> list[PullRequest]:
    """Fetch merged pull requests since a given date."""
    client = get_client(token)
    prs = execute_paginated_query(
        client,
        REPO_METRICS_QUERY,
        {"owner": org, "name": repo, "first": PAGE_SIZE},
        "repository.pullRequests",
    )

    result = []
    for pr in prs:
        mapped = _map_pull_request(pr)
        merged_at = mapped["merged_at"]
        if merged_at is None:
            continue
        if merged_at < since:  # type: ignore[operator]
            break

        result.append(mapped)

    return result


def fetch_reviews(
    token: str, org: str, repo: str, pr_numbers: list[int]
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


def fetch_repo_metrics(
    token: str, org: str, repo: str, since: datetime
) -> tuple[list[PullRequest], dict[int, list[Review]]]:
    """Fetch PRs and reviews in a single query."""
    client = get_client(token)
    prs = execute_paginated_query(
        client,
        REPO_METRICS_QUERY,
        {"owner": org, "name": repo, "first": PAGE_SIZE},
        "repository.pullRequests",
    )

    mapped_prs: list[PullRequest] = []
    reviews_by_pr: dict[int, list[Review]] = {}

    for pr in prs:
        mapped = _map_pull_request(pr)
        merged_at = mapped["merged_at"]
        if merged_at is None:
            continue
        if merged_at < since:  # type: ignore[operator]
            break

        pr_number = mapped["number"]
        mapped_prs.append(mapped)

        reviews = pr.get("reviews", {}).get("nodes", [])
        reviews_by_pr[pr_number] = [_map_review(r) for r in reviews]

    return mapped_prs, reviews_by_pr

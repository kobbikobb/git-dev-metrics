from datetime import datetime

from ..models import OpenPullRequest, PullRequest, Repository, Review
from .graphql_client import execute_paginated_query, get_client
from .graphql_queries import (
    OPEN_PRS_QUERY,
    ORG_REPOSITORIES_QUERY,
    REPO_METRICS_QUERY,
    REPOSITORIES_QUERY,
    SEARCH_MERGED_PRS_QUERY,
)

PAGE_SIZE = 50


def _build_merged_prs_query(org: str, repo: str, since: datetime) -> str:
    """Build GitHub search query for PRs merged after a date."""
    since_str = since.strftime("%Y-%m-%d")
    return f"repo:{org}/{repo} is:pr merged:>={since_str}"


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


def fetch_pull_requests(token: str, org: str, repo: str, since: datetime) -> list[PullRequest]:
    """Fetch merged pull requests since a given date using search API."""
    client = get_client(token)
    search_query = _build_merged_prs_query(org, repo, since)
    prs = execute_paginated_query(
        client,
        SEARCH_MERGED_PRS_QUERY,
        {"query": search_query, "first": PAGE_SIZE},
        "search",
    )

    return [_map_pull_request(pr) for pr in prs if pr.get("mergedAt")]


def fetch_reviews(
    token: str, org: str, repo: str, pr_numbers: list[int], since: datetime
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


def _filter_and_map_pr(prs: list[dict], since: datetime) -> tuple[list, dict]:
    """Filter PRs by date and map to internal format."""
    mapped_prs = []
    reviews_by_pr = {}

    for pr in prs:
        mapped = _map_pull_request(pr)
        merged_at = mapped["merged_at"]
        if merged_at is None or merged_at < since:  # type: ignore[reportOperatorIssue]
            continue

        pr_number = mapped["number"]
        mapped_prs.append(mapped)
        reviews = pr.get("reviews", {}).get("nodes", [])
        reviews_by_pr[pr_number] = [_map_review(r) for r in reviews]

    return mapped_prs, reviews_by_pr


def fetch_repo_metrics(
    token: str, org: str, repo: str, since: datetime
) -> tuple[list[PullRequest], dict[int, list[Review]]]:
    """Fetch PRs and reviews in a single query using search API."""
    client = get_client(token)
    search_query = _build_merged_prs_query(org, repo, since)
    prs = execute_paginated_query(
        client,
        SEARCH_MERGED_PRS_QUERY,
        {"query": search_query, "first": PAGE_SIZE},
        "search",
    )

    return _filter_and_map_pr(prs, since)


def fetch_open_prs(token: str, org: str, repo: str) -> list[OpenPullRequest]:
    """Fetch open pull requests for a repository."""
    client = get_client(token)
    prs = execute_paginated_query(
        client,
        OPEN_PRS_QUERY,
        {"owner": org, "name": repo, "first": PAGE_SIZE},
        "repository.pullRequests",
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

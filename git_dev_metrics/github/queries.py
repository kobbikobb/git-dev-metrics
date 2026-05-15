from ..models import OpenPullRequest, PullRequest, Repository, Review
from ..utils import TimePeriod
from ..utils.date_utils import parse_iso_datetime
from ._response_mapper import (
    map_author_login,
    map_pull_request,
    map_repository,
    map_review,
)
from .graphql_client import execute_paginated_query, get_client
from .graphql_queries import (
    OPEN_PRS_QUERY,
    ORG_REPOSITORIES_QUERY,
    REPO_METRICS_QUERY,
    REPOSITORIES_QUERY,
    SEARCH_MERGED_PRS_QUERY,
)

PAGE_SIZE = 50
SEARCH_PAGE_SIZE = 25


def _build_merged_prs_query(org: str, repo: str, period: TimePeriod) -> str:
    """Build GitHub search query for PRs merged within a TimePeriod."""
    since = period.since.strftime("%Y-%m-%d")
    until = period.until.strftime("%Y-%m-%d")
    return f"repo:{org}/{repo} is:pr merged:{since}..{until}"


def fetch_repositories(token: str) -> list[Repository]:
    """Fetch all repositories accessible with the given token."""
    client = get_client(token)
    repos = execute_paginated_query(
        client, REPOSITORIES_QUERY, {"first": PAGE_SIZE}, "viewer.repositories"
    )

    return [map_repository(repo) for repo in repos if repo.get("nameWithOwner")]


def fetch_org_repositories(token: str, org: str) -> list[Repository]:
    """Fetch all repositories for a specific organization."""
    client = get_client(token)
    repos = execute_paginated_query(
        client,
        ORG_REPOSITORIES_QUERY,
        {"login": org, "first": PAGE_SIZE},
        "organization.repositories",
    )

    return [map_repository(repo) for repo in repos if repo.get("nameWithOwner")]


def fetch_pull_requests(token: str, org: str, repo: str, period: TimePeriod) -> list[PullRequest]:
    """Fetch merged pull requests within a TimePeriod using search API."""
    client = get_client(token)
    search_query = _build_merged_prs_query(org, repo, period)
    prs = execute_paginated_query(
        client,
        SEARCH_MERGED_PRS_QUERY,
        {"query": search_query, "first": SEARCH_PAGE_SIZE},
        "search",
        repo_id=f"{org}/{repo}",
    )

    return [map_pull_request(pr) for pr in prs if pr.get("mergedAt")]


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
        reviews_by_pr[pr_number] = [map_review(r) for r in reviews]

    return reviews_by_pr


def _filter_and_map_pr(prs: list[dict], period: TimePeriod) -> list[PullRequest]:
    """Filter PRs by TimePeriod and attach reviews to each PR."""
    mapped_prs: list[PullRequest] = []

    for pr in prs:
        mapped = map_pull_request(pr)
        merged_at = mapped["merged_at"]
        if merged_at is None or merged_at < period.since or merged_at >= period.until:
            continue

        review_nodes = pr.get("reviews", {}).get("nodes", [])
        mapped["reviews"] = [map_review(r) for r in review_nodes]
        mapped_prs.append(mapped)

    return mapped_prs


def fetch_repo_metrics(token: str, org: str, repo: str, period: TimePeriod) -> list[PullRequest]:
    """Fetch PRs (with attached reviews) in a single query using search API."""
    client = get_client(token)
    search_query = _build_merged_prs_query(org, repo, period)
    prs = execute_paginated_query(
        client,
        SEARCH_MERGED_PRS_QUERY,
        {"query": search_query, "first": SEARCH_PAGE_SIZE},
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
                "created_at": parse_iso_datetime(pr.get("createdAt")),
                "merged_at": None,
                "user": {"login": map_author_login(pr.get("author"))},
                "is_draft": pr.get("isDraft", False),
                "is_approved": is_approved,
            }
        )
    return result

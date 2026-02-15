from datetime import datetime

import requests

from .type_definitions import (
    GitHubAPIError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    PullRequest,
    Repository,
)

GITHUB_API_URL = "https://api.github.com/user/repos"
GITHUB_API_VERSION = "2022-11-28"

MAX_REPOS_PER_PAGE = 100

GITHUB_PULLS_URL = "https://api.github.com/repos/{org}/{repo}/pulls"
GITHUB_COMMITS_URL = "https://api.github.com/repos/{org}/{repo}/commits"


def _get_api_headers(token: str) -> dict:
    """Build GitHub API request headers."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def _check_rate_limit(response: requests.Response) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None and int(remaining) == 0:
        reset_time = response.headers.get("X-RateLimit-Reset", "")
        raise GitHubRateLimitError(f"GitHub API rate limit exceeded. Resets at {reset_time}")


def fetch_repositories(token: str) -> list[Repository]:
    """Fetch all repositories for the authenticated user."""
    params = {"visibility": "all", "sort": "updated", "per_page": MAX_REPOS_PER_PAGE}

    response = requests.get(
        GITHUB_API_URL, headers=_get_api_headers(token), params=params, timeout=30
    )

    _check_rate_limit(response)

    if response.status_code == 401:
        raise GitHubAPIError("Unauthorized. Your token might be expired.")

    response.raise_for_status()

    return response.json()


def fetch_pull_requests(token: str, org: str, repo: str, since: datetime) -> list[PullRequest]:
    """Fetch pull requests for a repository within a time period."""
    # Even if filtering is not supported, we can sort by updated date
    # and stop once we reach PRs older than 'since'
    url = GITHUB_PULLS_URL.format(org=org, repo=repo)
    params = {
        "state": "closed",
        "sort": "updated",
        "direction": "desc",
        "per_page": 100,
    }

    all_prs = []

    while url:
        response = requests.get(url, headers=_get_api_headers(token), params=params, timeout=30)
        if response.status_code == 404:
            raise GitHubNotFoundError(f"Repository {org}/{repo} not found")

        _check_rate_limit(response)

        response.raise_for_status()
        prs = response.json()

        if not prs:
            break

        for pr in prs:
            if pr.get("merged_at"):
                merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                if merged_date >= since:
                    all_prs.append(pr)
                else:  # Since PRs are sorted ...
                    return all_prs

        # Follow pagination Link header
        url = response.links.get("next", {}).get("url")
        params = {}  # params are in the URL now

    return all_prs

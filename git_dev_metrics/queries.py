from datetime import datetime, timezone
from typing import List, Dict, Any, TypedDict
import requests

from .exceptions import GitHubAPIError, GitHubNotFoundError

GITHUB_API_URL = "https://api.github.com/user/repos"
GITHUB_API_VERSION = "2022-11-28"

MAX_REPOS_PER_PAGE = 100

GITHUB_PULLS_URL = "https://api.github.com/repos/{org}/{repo}/pulls"
GITHUB_COMMITS_URL = "https://api.github.com/repos/{org}/{repo}/commits"


class RepositoryPermissions(TypedDict):
    admin: bool
    push: bool
    pull: bool


class Repository(TypedDict):
    full_name: str
    private: bool
    permissions: RepositoryPermissions


def get_api_headers(token: str) -> dict:
    """Build GitHub API request headers."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def fetch_repositories(token: str) -> List[Repository]:
    """Fetch all repositories for the authenticated user."""
    params = {"visibility": "all", "sort": "updated", "per_page": MAX_REPOS_PER_PAGE}

    response = requests.get(
        GITHUB_API_URL, headers=get_api_headers(token), params=params
    )

    if response.status_code == 401:
        raise GitHubAPIError("Unauthorized. Your token might be expired.")

    response.raise_for_status()

    return response.json()


def fetch_pull_requests(
    token: str, org: str, repo: str, since: datetime
) -> List[Dict[Any, Any]]:
    """Fetch pull requests for a repository within a time period."""
    url = GITHUB_PULLS_URL.format(org=org, repo=repo)
    params = {
        "state": "closed",
        "sort": "updated",
        "direction": "desc",
        "per_page": 100,
    }
    # TODO: Handle pagination if more than 100 PRs are needed

    response = requests.get(url, headers=get_api_headers(token), params=params)

    if response.status_code == 404:
        raise GitHubNotFoundError(f"Repository {org}/{repo} not found")

    response.raise_for_status()
    prs = response.json()
    # Ensure since is timezone-aware for comparison
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)  # ← Add this line

    # TODO: Can we filter the PRs in the query?
    filtered_prs = []
    for pr in prs:
        if pr.get("merged_at"):
            merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            if merged_date >= since:
                filtered_prs.append(pr)

    return filtered_prs

from datetime import datetime, timezone
from typing import List
import requests
from .types import Repository, PullRequest, GitHubAPIError, GitHubNotFoundError
from .graphql_client import GitHubGraphQL

GITHUB_API_URL = "https://api.github.com/user/repos"
GITHUB_API_VERSION = "2022-11-28"

MAX_REPOS_PER_PAGE = 100

PULL_REQUESTS_QUERY = """
query($owner: String!, $name: String!, $since: DateTime!) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: MERGED, first: 100, orderBy: {field: MERGED_AT, direction: DESC}) {
      nodes {
        id
        number
        title
        state
        createdAt
        mergedAt
        closedAt
        additions
        deletions
        changedFiles
        author {
          login
        }
      }
    }
  }
}
"""


def get_api_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def fetch_repositories(token: str) -> List[Repository]:
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
) -> List[PullRequest]:
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    client = GitHubGraphQL(token)

    try:
        data = client.execute(
            PULL_REQUESTS_QUERY,
            {"owner": org, "name": repo, "since": since.isoformat()},
        )
    except Exception as e:
        if "Not Found" in str(e):
            raise GitHubNotFoundError(f"Repository {org}/{repo} not found")
        raise

    repository = data.get("data", {}).get("repository")
    if not repository:
        raise GitHubNotFoundError(f"Repository {org}/{repo} not found")

    prs = repository.get("pullRequests", {}).get("nodes", [])

    filtered_prs = []
    since_dt = since
    for pr in prs:
        merged_at = pr.get("mergedAt")
        if merged_at:
            merged_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            if merged_date >= since_dt:
                filtered_prs.append(
                    {
                        "id": pr.get("id"),
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "state": pr.get("state"),
                        "created_at": pr.get("createdAt"),
                        "merged_at": pr.get("mergedAt"),
                        "closed_at": pr.get("closedAt"),
                        "additions": pr.get("additions", 0),
                        "deletions": pr.get("deletions", 0),
                        "changed_files": pr.get("changedFiles", 0),
                        "user": {"login": pr.get("author", {}).get("login", "unknown")},
                    }
                )

    return filtered_prs

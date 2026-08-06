"""Repository metadata via REST — archived-state detection.

The stale report iterates repos cached by pull, which can outlive a repo
being archived. Archived repos accept no new PRs and expose no Dependabot
alerts, so their REST endpoints fail (403/404) even with a fully-scoped
token. Check archive state up front and skip the repo.
"""

import requests

from .exceptions import GitHubAPIError, GitHubAuthError, GitHubNotFoundError

REPO_URL = "https://api.github.com/repos/{org}/{repo}"
DEFAULT_TIMEOUT = 60


def is_repo_archived(token: str, org: str, repo: str) -> bool:
    """True when the repository is archived.

    Args:
        token: GitHub fine-grained access token (needs Metadata: Read).
        org: organization name.
        repo: repository name.

    Returns:
        True if the repo is archived, False otherwise.

    Raises:
        GitHubNotFoundError: repo not found.
        GitHubAuthError: token cannot read repository metadata.
        GitHubAPIError: request failed.
    """
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    response = session.get(REPO_URL.format(org=org, repo=repo), timeout=DEFAULT_TIMEOUT)
    if response.status_code == 404:
        raise GitHubNotFoundError(f"Repo {org}/{repo} not found")
    if response.status_code in (401, 403):
        raise GitHubAuthError(
            f"Token cannot read repo metadata for {org}/{repo} (needs Metadata: Read permission)"
        )
    if response.status_code >= 400:
        raise GitHubAPIError(
            f"Failed to fetch repo status for {org}/{repo}: HTTP {response.status_code}"
        )
    return bool(response.json().get("archived"))

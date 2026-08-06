"""GitHub Actions workflow runs via REST — CI build status.

Build status is read from Actions workflow runs (requires the Actions: Read
permission on a fine-grained token) instead of GraphQL statusCheckRollup,
which needs Checks access that fine-grained tokens cannot be granted.
Stale PRs are few per repo, so one workflow-runs request per head SHA is
cheap and avoids the shallow-history problem of listing runs repo-wide.
"""

import requests

from .exceptions import GitHubAPIError, GitHubAuthError, GitHubNotFoundError

ACTIONS_RUNS_URL = "https://api.github.com/repos/{org}/{repo}/actions/runs"
DEFAULT_TIMEOUT = 60
PAGE_SIZE = 100


def _build_state_from_runs(runs: list[dict]) -> str | None:
    """Map workflow runs for one head SHA to a build state.

    PENDING while any run is still in progress; SUCCESS only when every run
    completed successfully; otherwise FAILURE. Returns None when no runs exist.
    """
    if not runs:
        return None
    if any(run.get("status") != "completed" for run in runs):
        return "PENDING"
    conclusions = {run.get("conclusion") for run in runs}
    return "SUCCESS" if conclusions == {"success"} else "FAILURE"


def fetch_open_pr_build_state(
    token: str, org: str, repo: str, numbers_to_sha: dict[int, str | None]
) -> dict[int, str]:
    """Fetch Actions workflow-run state per PR, keyed by PR number.

    Args:
        token: GitHub fine-grained access token (needs Actions: Read).
        org: organization name.
        repo: repository name.
        numbers_to_sha: PR number to head commit SHA.

    Returns:
        Mapping of PR number to "SUCCESS", "FAILURE", or "PENDING". PRs with
        no workflow runs for their head SHA are omitted.

    Raises:
        GitHubNotFoundError: repo not found.
        GitHubAuthError: token cannot read workflow runs.
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

    result: dict[int, str] = {}
    for number, sha in numbers_to_sha.items():
        if not sha:
            continue
        response = session.get(
            ACTIONS_RUNS_URL.format(org=org, repo=repo),
            params={"head_sha": sha, "per_page": PAGE_SIZE},
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code == 404:
            raise GitHubNotFoundError(f"Repo {org}/{repo} not found")
        if response.status_code in (401, 403):
            raise GitHubAuthError(
                f"Token cannot read workflow runs for {org}/{repo} (needs Actions: Read permission)"
            )
        if response.status_code >= 400:
            raise GitHubAPIError(
                f"Failed to fetch workflow runs for {org}/{repo}: HTTP {response.status_code}"
            )
        state = _build_state_from_runs(response.json().get("workflow_runs", []))
        if state:
            result[number] = state
    return result

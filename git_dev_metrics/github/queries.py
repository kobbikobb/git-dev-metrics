from datetime import UTC, datetime

from github import Github, GithubException

from ..models import PullRequest, Repository
from .exceptions import GitHubAPIError, GitHubNotFoundError


def fetch_repositories(token: str) -> list[Repository]:
    """Fetch all repositories accessible with the given token."""
    try:
        g = Github(token)
        user = g.get_user()
        repos = user.get_repos(sort="updated", direction="desc")

        return [
            {
                "full_name": repo.full_name,
                "private": repo.private,
                "last_pushed": repo.pushed_at
            }
            for repo in repos
        ]
    except GithubException as e:
        if e.status == 401:
            raise GitHubAPIError("Unauthorized. Your token might be expired.") from e
        raise GitHubAPIError(f"GitHub API error: {e.data.get('message', str(e))}") from e


def fetch_pull_requests(token: str, org: str, repo: str, since: datetime) -> list[PullRequest]:
    """Fetch merged pull requests since a given date."""
    since = since.replace(tzinfo=UTC) if since.tzinfo is None else since

    try:
        g = Github(token)
        repository = g.get_repo(f"{org}/{repo}")

        # Get closed PRs (which includes merged ones)
        pulls = repository.get_pulls(state="closed", sort="updated", direction="desc")

        result = []
        for pr in pulls:
            # Only include merged PRs
            if not pr.merged_at:
                continue

            # Stop fetching if we've gone past our date range
            if pr.merged_at < since:
                break

            result.append(
                {
                    "number": pr.number,
                    "title": pr.title,
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files,
                    "user": {"login": pr.user.login if pr.user else "unknown"},
                }
            )

        return result

    except GithubException as e:
        if e.status == 404:
            raise GitHubNotFoundError(f"Repository {org}/{repo} not found") from e
        raise GitHubAPIError(f"GitHub API error: {e.data.get('message', str(e))}") from e

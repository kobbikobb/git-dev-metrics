from typing import TypedDict


class RepositoryPermissions(TypedDict):
    admin: bool
    push: bool
    pull: bool


class Repository(TypedDict):
    full_name: str
    private: bool
    permissions: RepositoryPermissions


class GitHubUser(TypedDict):
    login: str


class PullRequest(TypedDict):
    id: int
    number: int
    state: str
    title: str
    user: GitHubUser
    created_at: str
    merged_at: str
    created_at: str
    closed_at: str
    additions: int
    deletions: int
    changed_files: int


class GitHubError(Exception):
    """Base exception for GitHub API errors."""

    pass


class GitHubAuthError(GitHubError):
    """Authentication failed."""

    pass


class GitHubAPIError(GitHubError):
    """API request failed."""

    pass


class GitHubRateLimitError(GitHubAPIError):
    """Rate limit exceeded."""

    pass


class GitHubNotFoundError(GitHubAPIError):
    """Resource not found."""

    pass

"""Custom exceptions for git-dev-metrics."""


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

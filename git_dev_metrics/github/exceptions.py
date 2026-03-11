class GitHubError(Exception):
    """Base exception for GitHub API errors."""

    pass


class GitHubAPIError(GitHubError):
    """API request failed."""

    pass


class GitHubAuthError(GitHubAPIError):
    """Authentication failed."""

    pass


class GitHubRateLimitError(GitHubAPIError):
    """Rate limit exceeded."""

    pass


class GitHubNotFoundError(GitHubAPIError):
    """Resource not found."""

    pass

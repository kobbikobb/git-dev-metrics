"""Git development metrics collection tool."""

__version__ = "0.1.0"

from .client import GitHubClient
from .type_definitions import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)

__all__ = [
    "GitHubClient",
    "GitHubError",
    "GitHubAuthError",
    "GitHubAPIError",
    "GitHubRateLimitError",
    "GitHubNotFoundError",
]

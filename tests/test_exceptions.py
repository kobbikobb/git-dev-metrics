"""Unit tests for exceptions.py classes."""

import pytest
from git_dev_metrics.exceptions import (
    GitHubError,
    GitHubAuthError,
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubNotFoundError,
)


class TestGitHubError:
    """Test cases for GitHubError base exception."""

    def test_should_inherit_from_exception(self):
        # Arrange & Act & Assert
        assert issubclass(GitHubError, Exception)

    def test_should_create_instance_with_message(self):
        # Arrange
        message = "Test error message"

        # Act
        error = GitHubError(message)

        # Assert
        assert str(error) == message

    def test_should_create_instance_without_message(self):
        # Arrange & Act
        error = GitHubError()

        # Assert
        assert str(error) == ""


class TestGitHubAuthError:
    """Test cases for GitHubAuthError."""

    def test_should_inherit_from_github_error(self):
        # Arrange & Act & Assert
        assert issubclass(GitHubAuthError, GitHubError)

    def test_should_create_instance_with_auth_message(self):
        # Arrange
        message = "Authentication failed"

        # Act
        error = GitHubAuthError(message)

        # Assert
        assert str(error) == message


class TestGitHubAPIError:
    """Test cases for GitHubAPIError."""

    def test_should_inherit_from_github_error(self):
        # Arrange & Act & Assert
        assert issubclass(GitHubAPIError, GitHubError)

    def test_should_create_instance_with_api_message(self):
        # Arrange
        message = "API request failed"

        # Act
        error = GitHubAPIError(message)

        # Assert
        assert str(error) == message


class TestGitHubRateLimitError:
    """Test cases for GitHubRateLimitError."""

    def test_should_inherit_from_github_api_error(self):
        # Arrange & Act & Assert
        assert issubclass(GitHubRateLimitError, GitHubAPIError)

    def test_should_create_instance_with_rate_limit_message(self):
        # Arrange
        message = "Rate limit exceeded"

        # Act
        error = GitHubRateLimitError(message)

        # Assert
        assert str(error) == message


class TestGitHubNotFoundError:
    """Test cases for GitHubNotFoundError."""

    def test_should_inherit_from_github_api_error(self):
        # Arrange & Act & Assert
        assert issubclass(GitHubNotFoundError, GitHubAPIError)

    def test_should_create_instance_with_not_found_message(self):
        # Arrange
        message = "Resource not found"

        # Act
        error = GitHubNotFoundError(message)

        # Assert
        assert str(error) == message

    def test_should_be_catchable_as_parent_types(self):
        # Arrange
        message = "Not found"

        # Act
        error = GitHubNotFoundError(message)

        # Assert
        assert isinstance(error, GitHubNotFoundError)
        assert isinstance(error, GitHubAPIError)
        assert isinstance(error, GitHubError)
        assert isinstance(error, Exception)

"""Tests for repository metadata REST client."""

import re

import pytest
import responses

from git_dev_metrics.github import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubNotFoundError,
    is_repo_archived,
)


class TestIsRepoArchived:
    @responses.activate
    def test_should_return_true_for_archived_repo(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo"),
            json={"name": "myrepo", "archived": True},
            status=200,
        )

        assert is_repo_archived("fake-token", "myorg", "myrepo") is True

    @responses.activate
    def test_should_return_false_for_active_repo(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo"),
            json={"name": "myrepo", "archived": False},
            status=200,
        )

        assert is_repo_archived("fake-token", "myorg", "myrepo") is False

    @responses.activate
    def test_should_raise_not_found_on_404(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo"),
            status=404,
        )

        with pytest.raises(GitHubNotFoundError):
            is_repo_archived("fake-token", "myorg", "myrepo")

    @responses.activate
    def test_should_raise_auth_error_on_403(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo"),
            status=403,
        )

        with pytest.raises(GitHubAuthError, match="Metadata: Read"):
            is_repo_archived("fake-token", "myorg", "myrepo")

    @responses.activate
    def test_should_raise_api_error_on_500(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo"),
            status=500,
        )

        with pytest.raises(GitHubAPIError):
            is_repo_archived("fake-token", "myorg", "myrepo")

import responses
from git_dev_metrics.queries import fetch_repositories, fetch_pull_requests
from git_dev_metrics.types import GitHubAPIError
from .conftest import any_pr
from pytest import raises
from datetime import datetime, timezone


class TestFetchRepositories:
    @responses.activate
    def test_should_return_repositories(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user/repos",
            json=[{"name": "my-repo", "full_name": "user/my-repo"}],
            status=200,
        )

        result = fetch_repositories("fake-token")

        assert len(result) == 1
        assert result[0]["full_name"] == "user/my-repo"

    @responses.activate
    def test_should_raise_on_unauthorized(self):
        responses.add(responses.GET, "https://api.github.com/user/repos", status=401)

        with raises(GitHubAPIError, match="Unauthorized"):
            fetch_repositories("bad-token")

    @responses.activate
    def test_should_return_pr(self):
        pr = any_pr(merged_at="2024-01-02T00:00:00Z")
        responses.add(
            responses.GET,
            "https://api.github.com/repos/facebook/react/pulls",
            json=[pr],
            status=200,
        )
        since = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        result = fetch_pull_requests("fake-token", "facebook", "react", since)

        assert len(result) == 1

    @responses.activate
    def test_should_not_return_pr_merged_before(self):
        pr = any_pr(merged_at="2024-02-01T00:00:00Z") 

        responses.add(
            responses.GET,
            "https://api.github.com/repos/facebook/react/pulls",
            json=[pr],
            status=200,
        )
        since = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

        result = fetch_pull_requests("fake-token", "facebook", "react", since)

        assert len(result) == 0

import responses
from git_dev_metrics.queries import fetch_repositories, fetch_pull_requests
from git_dev_metrics.types import GitHubAPIError
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
        pr = {
            "id": 123,
            "number": 1,
            "state": "closed",
            "title": "Fix bug",
            "user": {"login": "contributor"},
            "created_at": "2024-01-01T00:00:00Z",
            "merged_at": "2024-01-02T00:00:00Z",
            "closed_at": "2024-01-02T00:00:00Z",
            "additions": 10,
            "deletions": 2,
            "changed_files": 1,
        }

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
        pr = {
            "id": 123,
            "number": 1,
            "state": "closed",
            "title": "Fix bug",
            "user": {"login": "contributor"},
            "created_at": "2024-01-01T00:00:00Z",
            "merged_at": "2024-01-02T00:00:00Z",
            "closed_at": "2024-01-02T00:00:00Z",
            "additions": 10,
            "deletions": 2,
            "changed_files": 1,
        }

        responses.add(
            responses.GET,
            "https://api.github.com/repos/facebook/react/pulls",
            json=[pr],
            status=200,
        )
        since = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

        result = fetch_pull_requests("fake-token", "facebook", "react", since)

        assert len(result) == 0

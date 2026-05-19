import re

import responses
from pytest import raises

from git_dev_metrics.github import (
    GitHubAPIError,
    fetch_pull_requests,
    fetch_repositories,
    fetch_reviews,
)
from git_dev_metrics.utils import TimePeriod

from ..conftest import dt


class TestFetchRepositories:
    @responses.activate
    def test_should_return_repositories(self):
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "viewer": {
                        "repositories": {
                            "nodes": [
                                {
                                    "nameWithOwner": "user/my-repo",
                                    "isPrivate": False,
                                    "pushedAt": "2024-01-01T00:00:00Z",
                                }
                            ]
                        }
                    }
                }
            },
            status=200,
        )

        result = fetch_repositories("fake-token")

        assert len(result) == 1
        assert result[0]["full_name"] == "user/my-repo"

    @responses.activate
    def test_should_raise_on_unauthorized(self):
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={"errors": [{"type": "UNAUTHORIZED", "message": "Authentication failed"}]},
            status=200,
        )

        with raises(GitHubAPIError, match="Unauthorized"):
            fetch_repositories("bad-token")

    @responses.activate
    def test_should_return_pr(self):
        pr = {
            "number": 1,
            "title": "Test PR",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": "2024-01-02T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "testuser"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
        }
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "search": {"nodes": [pr], "pageInfo": {"hasNextPage": False, "endCursor": None}}
                }
            },
            status=200,
        )
        period = TimePeriod(
            since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)
        )

        result = fetch_pull_requests("fake-token", "facebook", "react", period)

        assert len(result) == 1

    @responses.activate
    def test_should_not_return_pr_merged_before(self):
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "search": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
                }
            },
            status=200,
        )
        period = TimePeriod(
            since=dt(year=2024, month=3, day=1), until=dt(year=2024, month=4, day=1)
        )

        result = fetch_pull_requests("fake-token", "facebook", "react", period)

        assert len(result) == 0


class TestFetchReviews:
    @responses.activate
    def test_should_return_reviews(self):
        pr_with_reviews = {
            "number": 1,
            "mergedAt": "2024-01-02T00:00:00Z",
            "reviews": {
                "nodes": [
                    {
                        "author": {"login": "reviewer1"},
                        "state": "APPROVED",
                        "submittedAt": "2024-01-02T01:00:00Z",
                    }
                ]
            },
        }
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr_with_reviews],
                            "pageInfo": {"hasNextPage": False, "endCursor": "cursor1"},
                        }
                    }
                }
            },
            status=200,
        )

        result = fetch_reviews(
            "fake-token",
            "facebook",
            "react",
            [1],
            TimePeriod(since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)),
        )

        assert len(result) == 1
        assert 1 in result
        assert len(result[1]) == 1
        assert result[1][0]["user"]["login"] == "reviewer1"

    @responses.activate
    def test_should_return_empty_for_no_reviews(self):
        pr_no_reviews = {
            "number": 1,
            "mergedAt": "2024-01-02T00:00:00Z",
            "reviews": {"nodes": []},
        }
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr_no_reviews],
                            "pageInfo": {"hasNextPage": False, "endCursor": "cursor1"},
                        }
                    }
                }
            },
            status=200,
        )

        result = fetch_reviews(
            "fake-token",
            "facebook",
            "react",
            [1],
            TimePeriod(since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)),
        )

        assert 1 in result
        assert len(result[1]) == 0

    @responses.activate
    def test_should_return_empty_for_empty_pr_list(self):
        result = fetch_reviews(
            "fake-token",
            "facebook",
            "react",
            [],
            TimePeriod(since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)),
        )

        assert result == {}

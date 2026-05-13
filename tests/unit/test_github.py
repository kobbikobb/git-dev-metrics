import re

import responses
from pytest import raises

from git_dev_metrics.github import (
    GitHubAPIError,
    fetch_pull_requests,
    fetch_repositories,
    fetch_reviews,
)
from git_dev_metrics.github.graphql_client import execute_paginated_query, get_client
from git_dev_metrics.github.graphql_queries import REPO_METRICS_QUERY
from git_dev_metrics.utils import TimePeriod

from .conftest import dt


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
        # Search API filters by merged date server-side, so GitHub returns empty
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


class TestPagination:
    @responses.activate
    def test_should_fetch_all_pages_when_has_next_page(self):
        pr1 = {
            "number": 1,
            "title": "PR 1",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": "2024-01-02T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "user1"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
        }
        pr2 = {
            "number": 2,
            "title": "PR 2",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": "2024-01-03T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "user2"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
        }

        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr1],
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                        }
                    }
                }
            },
            status=200,
        )
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr2],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        client = get_client("fake-token")
        result = execute_paginated_query(
            client,
            REPO_METRICS_QUERY,
            {"owner": "test-org", "name": "test-repo", "first": 1},
            "repository.pullRequests",
        )

        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[1]["number"] == 2
        assert len(responses.calls) == 2

    @responses.activate
    def test_should_stop_after_first_page_when_no_next_page(self):
        pr = {
            "number": 1,
            "title": "PR 1",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": "2024-01-02T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "user1"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
        }

        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        client = get_client("fake-token")
        result = execute_paginated_query(
            client,
            REPO_METRICS_QUERY,
            {"owner": "test-org", "name": "test-repo", "first": 100},
            "repository.pullRequests",
        )

        assert len(result) == 1
        assert len(responses.calls) == 1

    @responses.activate
    def test_should_respect_page_size_override(self):
        pr1 = {"number": 1, "title": "PR 1"}
        pr2 = {"number": 2, "title": "PR 2"}

        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr1],
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                        }
                    }
                }
            },
            status=200,
        )
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr2],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        client = get_client("fake-token")
        result = execute_paginated_query(
            client,
            REPO_METRICS_QUERY,
            {"owner": "test-org", "name": "test-repo", "first": 100},
            "repository.pullRequests",
            page_size=1,
        )

        assert len(result) == 2
        assert len(responses.calls) == 2

        first_request_body = responses.calls[0].request.body
        assert first_request_body is not None
        assert (
            "first" in first_request_body.decode()
            if isinstance(first_request_body, bytes)
            else "first" in first_request_body
        )

    @responses.activate
    def test_should_return_empty_list_when_no_results(self):
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        client = get_client("fake-token")
        result = execute_paginated_query(
            client,
            REPO_METRICS_QUERY,
            {"owner": "test-org", "name": "test-repo", "first": 100},
            "repository.pullRequests",
        )

        assert result == []
        assert len(responses.calls) == 1

    @responses.activate
    def test_should_stop_early_with_stop_if_callback(self):
        pr1 = {"number": 1, "title": "PR 1", "mergedAt": "2024-01-02T00:00:00Z"}
        pr2 = {"number": 2, "title": "PR 2", "mergedAt": "2024-01-03T00:00:00Z"}

        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [pr1, pr2],
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                        }
                    }
                }
            },
            status=200,
        )

        client = get_client("fake-token")
        result = execute_paginated_query(
            client,
            REPO_METRICS_QUERY,
            {"owner": "test-org", "name": "test-repo", "first": 100},
            "repository.pullRequests",
            stop_if=lambda node: node.get("number") == 1,
        )

        assert len(result) == 1
        assert result[0]["number"] == 1
        assert len(responses.calls) == 1


class TestRetryOnTransientErrors:
    @responses.activate
    def test_should_retry_then_succeed_on_504(self, monkeypatch):
        from git_dev_metrics.github import graphql_client

        monkeypatch.setattr(graphql_client.time, "sleep", lambda _: None)

        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={"message": "Gateway Timeout"},
            status=504,
        )
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        client = get_client("fake-token")
        result = execute_paginated_query(
            client,
            REPO_METRICS_QUERY,
            {"owner": "o", "name": "r", "first": 1},
            "repository.pullRequests",
        )

        assert result == []
        assert len(responses.calls) == 2

    @responses.activate
    def test_should_give_up_after_exhausting_retries(self, monkeypatch):
        from git_dev_metrics.github import graphql_client

        monkeypatch.setattr(graphql_client.time, "sleep", lambda _: None)

        for _ in range(graphql_client.TRANSIENT_RETRY_ATTEMPTS):
            responses.add(
                responses.POST,
                re.compile(r"https://api\.github\.com/graphql"),
                json={"message": "Gateway Timeout"},
                status=504,
            )

        client = get_client("fake-token")
        with raises(GitHubAPIError):
            execute_paginated_query(
                client,
                REPO_METRICS_QUERY,
                {"owner": "o", "name": "r", "first": 1},
                "repository.pullRequests",
            )

        assert len(responses.calls) == graphql_client.TRANSIENT_RETRY_ATTEMPTS

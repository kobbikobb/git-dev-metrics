import re

import responses

from git_dev_metrics.github import fetch_open_prs, fetch_org_repositories, fetch_repo_metrics
from git_dev_metrics.github.queries import _filter_and_map_pr, fetch_reviews
from git_dev_metrics.utils import TimePeriod

from ..conftest import dt


class TestFetchOrgRepositories:
    @responses.activate
    def test_should_return_org_repositories(self):
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "organization": {
                        "repositories": {
                            "nodes": [
                                {
                                    "nameWithOwner": "myorg/repo1",
                                    "isPrivate": False,
                                    "pushedAt": "2024-01-01T00:00:00Z",
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        result = fetch_org_repositories("fake-token", "myorg")

        assert len(result) == 1
        assert result[0]["full_name"] == "myorg/repo1"

    @responses.activate
    def test_should_return_empty_when_no_repos(self):
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "organization": {
                        "repositories": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        result = fetch_org_repositories("fake-token", "myorg")

        assert result == []

    @responses.activate
    def test_should_skip_repos_without_name_with_owner(self):
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "organization": {
                        "repositories": {
                            "nodes": [
                                {},
                                {
                                    "nameWithOwner": "myorg/repo1",
                                    "isPrivate": False,
                                    "pushedAt": "2024-01-01T00:00:00Z",
                                },
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            },
            status=200,
        )

        result = fetch_org_repositories("fake-token", "myorg")

        assert len(result) == 1
        assert result[0]["full_name"] == "myorg/repo1"


class TestFilterAndMapPr:
    def test_should_include_pr_within_period(self):
        pr = {
            "number": 1,
            "title": "Test PR",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": "2024-01-15T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "testuser"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        period = TimePeriod(
            since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)
        )

        result = _filter_and_map_pr([pr], period)

        assert len(result) == 1
        assert result[0]["number"] == 1

    def test_should_exclude_pr_without_merged_at(self):
        pr = {
            "number": 1,
            "title": "No merge date",
            "createdAt": "2024-01-01T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "testuser"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        period = TimePeriod(
            since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)
        )

        result = _filter_and_map_pr([pr], period)

        assert len(result) == 0

    def test_should_exclude_pr_merged_before_period(self):
        pr = {
            "number": 1,
            "title": "Old PR",
            "createdAt": "2023-12-01T00:00:00Z",
            "mergedAt": "2023-12-15T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "testuser"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        period = TimePeriod(
            since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)
        )

        result = _filter_and_map_pr([pr], period)

        assert len(result) == 0

    def test_should_exclude_pr_merged_on_or_after_until(self):
        pr = {
            "number": 1,
            "title": "Borderline PR",
            "createdAt": "2024-02-01T00:00:00Z",
            "mergedAt": "2024-02-01T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "testuser"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        period = TimePeriod(
            since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)
        )

        result = _filter_and_map_pr([pr], period)

        assert len(result) == 0

    def test_should_attach_reviews_to_pr(self):
        pr = {
            "number": 1,
            "title": "PR with reviews",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": "2024-01-15T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "testuser"},
            "commits": {"nodes": []},
            "reviews": {
                "nodes": [
                    {
                        "author": {"login": "reviewer1"},
                        "state": "APPROVED",
                        "submittedAt": "2024-01-16T00:00:00Z",
                    }
                ]
            },
            "timelineItems": {"nodes": []},
        }
        period = TimePeriod(
            since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)
        )

        result = _filter_and_map_pr([pr], period)

        assert len(result[0]["reviews"]) == 1
        assert result[0]["reviews"][0]["user"]["login"] == "reviewer1"


class TestFetchRepoMetrics:
    @responses.activate
    def test_should_return_prs_within_period(self):
        pr = {
            "number": 1,
            "title": "Test PR",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": "2024-01-15T00:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 2,
            "author": {"login": "testuser"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        responses.add(
            responses.POST,
            re.compile(r"https://api\.github\.com/graphql"),
            json={
                "data": {
                    "search": {
                        "nodes": [pr],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            },
            status=200,
        )
        period = TimePeriod(
            since=dt(year=2024, month=1, day=1), until=dt(year=2024, month=2, day=1)
        )

        result = fetch_repo_metrics("fake-token", "facebook", "react", period)

        assert len(result) == 1
        assert result[0]["number"] == 1


class TestFetchReviewsSkip:
    @responses.activate
    def test_should_skip_pr_not_in_requested_list(self):
        pr1 = {
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
        pr2 = {
            "number": 2,
            "mergedAt": "2024-01-03T00:00:00Z",
            "reviews": {
                "nodes": [
                    {
                        "author": {"login": "reviewer2"},
                        "state": "CHANGES_REQUESTED",
                        "submittedAt": "2024-01-03T01:00:00Z",
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
                            "nodes": [pr1, pr2],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
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
        assert 2 not in result
        assert len(result[1]) == 1


class TestFetchOpenPrs:
    @responses.activate
    def test_should_return_open_prs(self):
        pr = {
            "number": 1,
            "title": "Open PR",
            "createdAt": "2024-01-01T00:00:00Z",
            "isDraft": False,
            "author": {"login": "dev1"},
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

        result = fetch_open_prs("fake-token", "myorg", "myrepo")

        assert len(result) == 1
        assert result[0]["number"] == 1
        assert result[0]["title"] == "Open PR"
        assert result[0]["is_draft"] is False
        assert result[0]["is_approved"] is False

    @responses.activate
    def test_should_return_empty_when_no_open_prs(self):
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

        result = fetch_open_prs("fake-token", "myorg", "myrepo")

        assert result == []

    @responses.activate
    def test_should_skip_pr_without_number(self):
        pr = {
            "title": "No number",
            "createdAt": "2024-01-01T00:00:00Z",
            "isDraft": False,
            "author": {"login": "dev1"},
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

        result = fetch_open_prs("fake-token", "myorg", "myrepo")

        assert result == []

    @responses.activate
    def test_should_skip_pr_without_title(self):
        pr = {
            "number": 1,
            "createdAt": "2024-01-01T00:00:00Z",
            "isDraft": False,
            "author": {"login": "dev1"},
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

        result = fetch_open_prs("fake-token", "myorg", "myrepo")

        assert result == []

    @responses.activate
    def test_should_detect_approved_review(self):
        pr = {
            "number": 1,
            "title": "Approved PR",
            "createdAt": "2024-01-01T00:00:00Z",
            "isDraft": False,
            "author": {"login": "dev1"},
            "reviews": {"nodes": [{"state": "APPROVED"}]},
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

        result = fetch_open_prs("fake-token", "myorg", "myrepo")

        assert result[0]["is_approved"] is True

    @responses.activate
    def test_should_mark_pr_as_draft(self):
        pr = {
            "number": 1,
            "title": "Draft PR",
            "createdAt": "2024-01-01T00:00:00Z",
            "isDraft": True,
            "author": {"login": "dev1"},
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

        result = fetch_open_prs("fake-token", "myorg", "myrepo")

        assert result[0]["is_draft"] is True

    @responses.activate
    def test_should_use_quiet_mode(self):
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

        result = fetch_open_prs("fake-token", "myorg", "myrepo", quiet=True)

        assert result == []

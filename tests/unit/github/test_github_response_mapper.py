from datetime import UTC, datetime

from git_dev_metrics.github._response_mapper import (
    map_author_login,
    map_datetime,
    map_pull_request,
    map_repository,
    map_review,
)

from ..conftest import dt


class TestMapDatetime:
    def test_should_parse_iso_string(self) -> None:
        result = map_datetime("2024-01-01T12:00:00Z")
        assert result == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    def test_should_return_none_for_none(self) -> None:
        assert map_datetime(None) is None

    def test_should_return_none_for_empty_string(self) -> None:
        assert map_datetime("") is None

    def test_should_return_none_for_invalid_string(self) -> None:
        assert map_datetime("not-a-date") is None


class TestMapAuthorLogin:
    def test_should_return_login_for_known_author(self) -> None:
        assert map_author_login({"login": "alice"}) == "alice"

    def test_should_return_unknown_for_none(self) -> None:
        assert map_author_login(None) == "unknown"

    def test_should_return_unknown_for_empty_dict(self) -> None:
        assert map_author_login({}) == "unknown"

    def test_should_return_unknown_for_missing_login(self) -> None:
        assert map_author_login({"name": "bob"}) == "unknown"


class TestMapRepository:
    def test_should_map_full_repo(self) -> None:
        raw = {
            "nameWithOwner": "myorg/myrepo",
            "isPrivate": True,
            "pushedAt": "2024-06-15T10:00:00Z",
        }
        result = map_repository(raw)
        assert result == {
            "full_name": "myorg/myrepo",
            "private": True,
            "last_pushed": dt(year=2024, month=6, day=15, hour=10),
        }

    def test_should_map_public_repo_without_push(self) -> None:
        raw = {"nameWithOwner": "myorg/other", "isPrivate": False, "pushedAt": None}
        result = map_repository(raw)
        assert result == {
            "full_name": "myorg/other",
            "private": False,
            "last_pushed": None,
        }


class TestMapPullRequest:
    def test_should_map_full_pr_with_reviews(self) -> None:
        raw = {
            "number": 42,
            "title": "Fix the thing",
            "createdAt": "2024-01-01T08:00:00Z",
            "mergedAt": "2024-01-02T16:00:00Z",
            "additions": 100,
            "deletions": 50,
            "changedFiles": 5,
            "author": {"login": "alice"},
            "commits": {
                "nodes": [
                    {"commit": {"committedDate": "2024-01-01T06:00:00Z", "message": "wip"}},
                    {"commit": {"committedDate": "2024-01-01T07:00:00Z", "message": "fix: done"}},
                ]
            },
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        result = map_pull_request(raw)
        assert result["number"] == 42
        assert result["title"] == "Fix the thing"
        assert result["user"]["login"] == "alice"
        assert result["additions"] == 100
        assert result["deletions"] == 50
        assert result["changed_files"] == 5
        assert result["created_at"] == dt(year=2024, month=1, day=1, hour=8)
        assert result["merged_at"] == dt(year=2024, month=1, day=2, hour=16)
        assert result["commit_messages"] == ["wip", "fix: done"]
        assert result["reviews"] == []

    def test_should_map_minimal_pr(self) -> None:
        raw: dict = {
            "number": 1,
            "title": "Minimal",
            "createdAt": "2024-01-01T00:00:00Z",
            "mergedAt": None,
            "additions": 0,
            "deletions": 0,
            "changedFiles": 0,
            "author": None,
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        result = map_pull_request(raw)
        assert result["number"] == 1
        assert result["user"]["login"] == "unknown"
        assert result["merged_at"] is None
        assert result["first_commit_at"] is None
        assert result["ready_for_review_at"] is None
        assert result["body"] is None
        assert result["commit_messages"] == []

    def test_should_extract_ready_for_review_from_timeline(self) -> None:
        raw = {
            "number": 2,
            "title": "PR",
            "createdAt": "2024-01-01T08:00:00Z",
            "mergedAt": "2024-01-02T16:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 1,
            "author": {"login": "bob"},
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {
                "nodes": [
                    {"createdAt": "2024-01-01T10:00:00Z"},
                ]
            },
        }
        result = map_pull_request(raw)
        assert result["ready_for_review_at"] == dt(year=2024, month=1, day=1, hour=10)

    def test_should_use_oldest_commit_as_first_commit(self) -> None:
        raw = {
            "number": 3,
            "title": "Commits",
            "createdAt": "2024-01-03T08:00:00Z",
            "mergedAt": "2024-01-04T16:00:00Z",
            "additions": 10,
            "deletions": 5,
            "changedFiles": 1,
            "author": {"login": "carol"},
            "commits": {
                "nodes": [
                    {"commit": {"committedDate": "2024-01-03T07:00:00Z", "message": "b"}},
                    {"commit": {"committedDate": "2024-01-02T06:00:00Z", "message": "a"}},
                ]
            },
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        result = map_pull_request(raw)
        assert result["first_commit_at"] == dt(year=2024, month=1, day=2, hour=6)
        assert result["commit_messages"] == ["b", "a"]


class TestMapReview:
    def test_should_map_approved_review(self) -> None:
        raw = {
            "author": {"login": "reviewer1"},
            "state": "APPROVED",
            "submittedAt": "2024-01-02T12:00:00Z",
        }
        result = map_review(raw)
        assert result == {
            "user": {"login": "reviewer1"},
            "state": "APPROVED",
            "submitted_at": dt(year=2024, month=1, day=2, hour=12),
        }

    def test_should_map_review_without_author(self) -> None:
        raw: dict = {"author": None, "state": "COMMENTED", "submittedAt": "2024-01-02T12:00:00Z"}
        result = map_review(raw)
        assert result["user"]["login"] == "unknown"

    def test_should_map_review_without_submitted_at(self) -> None:
        raw: dict = {"author": {"login": "r"}, "state": "CHANGES_REQUESTED", "submittedAt": None}
        result = map_review(raw)
        assert result["submitted_at"] is None

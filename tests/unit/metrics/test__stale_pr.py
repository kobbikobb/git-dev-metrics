"""Tests for stale PR detection."""

from datetime import UTC, datetime, timedelta
from typing import cast

from git_dev_metrics.models import OpenPullRequest, SecurityInfo


class TestGetStalePrs:
    def test_should_return_empty_for_empty_list(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        result = get_stale_prs([], "myrepo")
        assert result == []

    def test_should_use_custom_threshold(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "5 day old PR",
                    "created_at": now - timedelta(days=5),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
            ],
        )
        # 5 days = 120 hours, threshold 96h should flag it
        result = get_stale_prs(prs, "myrepo", lambda: now, threshold_hours=96)
        assert len(result) == 1
        # threshold 144h should not flag it
        result = get_stale_prs(prs, "myrepo", lambda: now, threshold_hours=144)
        assert result == []

    def test_should_return_fresh_prs(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "Fresh PR",
                    "created_at": now - timedelta(days=1),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert result == []

    def test_should_identify_stale_prs(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "Stale PR",
                    "created_at": now - timedelta(days=10),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert len(result) == 1
        assert result[0].number == 1
        assert result[0].author == "alice"
        assert result[0].repo == "myrepo"
        assert result[0].age_hours > 24 * 7

    def test_should_sort_by_creator_then_age_oldest_first(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "alice newer",
                    "created_at": now - timedelta(days=8),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
                {
                    "number": 2,
                    "title": "bob older",
                    "created_at": now - timedelta(days=15),
                    "merged_at": None,
                    "user": {"login": "bob"},
                },
                {
                    "number": 3,
                    "title": "alice older",
                    "created_at": now - timedelta(days=12),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        # Grouped by creator (alice before bob), oldest first within each creator
        assert [r.number for r in result] == [3, 1, 2]
        assert [r.author for r in result] == ["alice", "alice", "bob"]
        assert result[0].repo == "myrepo"

    def test_should_carry_labels(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "Stale with labels",
                    "created_at": now - timedelta(days=10),
                    "merged_at": None,
                    "user": {"login": "alice"},
                    "labels": ["bug", "priority:high"],
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert len(result) == 1
        assert result[0].labels == ("bug", "priority:high")

    def test_should_carry_build_state_and_security(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 7,
                    "title": "Stale with signals",
                    "created_at": now - timedelta(days=10),
                    "merged_at": None,
                    "user": {"login": "alice"},
                    "build_state": "FAILURE",
                },
            ],
        )
        security: dict[int, SecurityInfo] = {
            7: {"severity": "critical", "advisory_id": "GHSA-abcd"}
        }
        result = get_stale_prs(prs, "myrepo", lambda: now, security=security)
        assert len(result) == 1
        assert result[0].build_state == "FAILURE"
        assert result[0].security_severity == "critical"
        assert result[0].security_advisory == "GHSA-abcd"

    def test_should_leave_security_blank_when_no_join(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 7,
                    "title": "Stale without alerts",
                    "created_at": now - timedelta(days=10),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert len(result) == 1
        assert result[0].security_severity is None
        assert result[0].security_advisory is None


class TestSummarizeStalePrs:
    def test_should_return_zero_for_empty_list(self):
        from git_dev_metrics.metrics._stale_pr import summarize_stale_prs

        assert summarize_stale_prs([]) == (0, 0.0)

    def test_should_compute_count_and_mean_age(self):
        from git_dev_metrics.metrics._stale_pr import StalePr, summarize_stale_prs

        prs = [
            StalePr(
                number=1,
                title="a",
                author="x",
                repo="r",
                age_hours=480,
                age_days=20.0,
                is_draft=False,
                is_approved=False,
                url="",
            ),
            StalePr(
                number=2,
                title="b",
                author="y",
                repo="r",
                age_hours=240,
                age_days=10.0,
                is_draft=False,
                is_approved=False,
                url="",
            ),
        ]
        assert summarize_stale_prs(prs) == (2, 15.0)

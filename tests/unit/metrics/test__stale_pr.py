"""Tests for stale PR detection."""

from datetime import UTC, datetime, timedelta
from typing import cast

from git_dev_metrics.models import OpenPullRequest


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

    def test_should_sort_by_age_oldest_first(self):
        from git_dev_metrics.metrics._stale_pr import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "Newer stale",
                    "created_at": now - timedelta(days=8),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
                {
                    "number": 2,
                    "title": "Older stale",
                    "created_at": now - timedelta(days=15),
                    "merged_at": None,
                    "user": {"login": "bob"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert result[0].number == 2
        assert result[1].number == 1
        assert result[0].repo == "myrepo"


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

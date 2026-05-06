"""Unit tests for reports.py functions."""

from typing import cast

from git_dev_metrics.metrics import (
    calculate_avg_lines_per_pr,
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_throughput,
    median,
)
from git_dev_metrics.metrics.analyzer import _parse_period_days
from git_dev_metrics.models import OpenPullRequest

from .conftest import any_pr


class TestMedian:
    """Test cases for median helper function."""

    def test_should_return_zero_for_empty_list(self):
        result = median([])
        assert result == 0.0

    def test_should_return_value_for_single_element(self):
        result = median([5.0])
        assert result == 5.0

    def test_should_return_median_for_odd_count(self):
        result = median([1.0, 2.0, 3.0])
        assert result == 2.0

    def test_should_return_median_for_even_count(self):
        result = median([1.0, 2.0, 3.0, 4.0])
        assert result == 2.5

    def test_should_handle_integers(self):
        result = median([1, 2, 3])
        assert result == 2.0


class TestCalculateCycleTime:
    """Test cases for calculate_cycle_time function."""

    def test_should_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_cycle_time(prs)
        assert result == 0.0

    def test_should_return_correct_cycle_time_for_single_pr(self):
        prs = [any_pr(created_at="2024-01-01T00:00:00Z", merged_at="2024-01-02T00:00:00Z")]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_return_average_cycle_time_for_multiple_prs(self):
        prs = [
            any_pr(created_at="2024-01-01T00:00:00Z", merged_at="2024-01-02T00:00:00Z"),
            any_pr(created_at="2024-01-01T00:00:00Z", merged_at="2024-01-03T00:00:00Z"),
        ]

        result = calculate_cycle_time(prs)

        assert result == 36.0

    def test_should_handle_prs_with_different_time_zones(self):
        prs = [
            any_pr(created_at="2024-01-01T12:00:00Z", merged_at="2024-01-02T12:00:00Z"),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_use_first_commit_when_older_than_created_at(self):
        prs = [
            any_pr(
                created_at="2024-01-02T00:00:00Z",
                merged_at="2024-01-03T00:00:00Z",
                first_commit_at="2024-01-01T00:00:00Z",
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_use_created_at_when_older_than_first_commit(self):
        prs = [
            any_pr(
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-03T00:00:00Z",
                first_commit_at="2024-01-02T00:00:00Z",
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_use_created_at_when_first_commit_is_none(self):
        prs = [
            any_pr(
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-02T00:00:00Z",
                first_commit_at=None,
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_exclude_draft_window_using_ready_for_review_at(self):
        prs = [
            any_pr(
                created_at="2024-01-01T00:00:00Z",
                ready_for_review_at="2024-01-04T00:00:00Z",
                merged_at="2024-01-05T00:00:00Z",
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_ignore_ready_for_review_when_before_start_time(self):
        prs = [
            any_pr(
                created_at="2024-01-02T00:00:00Z",
                first_commit_at="2024-01-01T00:00:00Z",
                ready_for_review_at="2023-12-31T00:00:00Z",
                merged_at="2024-01-03T00:00:00Z",
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0


class TestCalculatePrSize:
    """Test cases for calculate_pr_size function."""

    def test_should_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_pr_size(prs)
        assert result == 0

    def test_should_return_correct_size_for_single_pr(self):
        prs = [any_pr(additions=100, deletions=50)]
        result = calculate_pr_size(prs)
        assert result == 150

    def test_should_return_average_size_for_multiple_prs(self):
        prs = [
            any_pr(additions=100, deletions=50),
            any_pr(additions=200, deletions=100),
        ]
        result = calculate_pr_size(prs)
        assert result == 225

    def test_should_return_median_size_not_mean(self):
        prs = [
            any_pr(additions=100, deletions=0),
            any_pr(additions=200, deletions=0),
            any_pr(additions=1000, deletions=0),
        ]
        result = calculate_pr_size(prs)
        assert result == 200

    def test_should_use_absolute_values_for_deletions(self):
        prs = [any_pr(additions=100, deletions=-50)]
        result = calculate_pr_size(prs)
        assert result == 150


class TestCalculateAvgLinesPerPr:
    """Test cases for calculate_avg_lines_per_pr function."""

    def test_should_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_avg_lines_per_pr(prs)
        assert result == 0.0

    def test_should_return_correct_avg_for_single_pr(self):
        prs = [any_pr(additions=100, deletions=50)]
        result = calculate_avg_lines_per_pr(prs)
        assert result == 150.0

    def test_should_return_mean_not_median(self):
        prs = [
            any_pr(additions=100, deletions=0),
            any_pr(additions=200, deletions=0),
            any_pr(additions=300, deletions=0),
        ]
        result = calculate_avg_lines_per_pr(prs)
        assert result == 200.0

    def test_should_use_absolute_values_for_deletions(self):
        prs = [any_pr(additions=100, deletions=-50)]
        result = calculate_avg_lines_per_pr(prs)
        assert result == 150.0


class TestCalculateThroughput:
    """Test cases for calculate_throughput function."""

    def test_should_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_throughput(prs)
        assert result == 0

    def test_should_return_count_of_prs(self):
        prs = [any_pr(id=2, number=2), any_pr(id=3, number=3)]
        result = calculate_throughput(prs)
        assert result == 2


class TestCalculatePickupTime:
    """Test cases for calculate_pickup_time function."""

    def test_should_return_zero_when_no_prs_provided(self):
        result = calculate_pickup_time([])
        assert result == 0.0

    def test_should_return_zero_when_no_reviews(self):
        prs = [
            any_pr(
                number=1,
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-02T00:00:00Z",
                reviews=[],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(
                number=1,
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-02T00:00:00Z",
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "COMMENTED",
                        "submitted_at": "2024-01-01T12:00:00Z",
                    }
                ],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 0.0

    def test_should_calculate_pickup_time(self):
        prs = [
            any_pr(
                number=1,
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-02T00:00:00Z",
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T12:00:00Z",
                    }
                ],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 12.0


class TestCalculateReviewTime:
    """Test cases for calculate_review_time function."""

    def test_should_return_zero_when_no_prs_provided(self):
        result = calculate_review_time([])
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(
                number=1,
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-02T00:00:00Z",
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "COMMENTED",
                        "submitted_at": "2024-01-01T12:00:00Z",
                    }
                ],
            )
        ]
        result = calculate_review_time(prs)
        assert result == 0.0

    def test_should_calculate_review_time(self):
        prs = [
            any_pr(
                number=1,
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-03T00:00:00Z",
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-02T00:00:00Z",
                    }
                ],
            )
        ]
        result = calculate_review_time(prs)
        assert result == 24.0


class TestCalculatePrsPerWeek:
    """Test cases for calculate_prs_per_week function."""

    def test_should_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_prs_per_week(prs, 30)
        assert result == 0.0

    def test_should_calculate_prs_per_week(self):
        prs = [any_pr(id=1, number=1), any_pr(id=2, number=2)]
        result = calculate_prs_per_week(prs, 14)
        assert result == 1.0

    def test_should_use_minimum_of_one_week(self):
        prs = [any_pr(id=1, number=1)]
        result = calculate_prs_per_week(prs, 3)
        assert result == 1.0


class TestParsePeriodDays:
    """Test cases for _parse_period_days function."""

    def test_should_parse_days(self):
        assert _parse_period_days("30d") == 30

    def test_should_parse_weeks(self):
        assert _parse_period_days("2w") == 14

    def test_should_parse_months(self):
        assert _parse_period_days("1m") == 30

    def test_should_default_to_30_for_invalid(self):
        assert _parse_period_days("invalid") == 30


class TestCalculateReviewsGiven:
    """Test cases for calculate_reviews_given function."""

    def test_should_return_empty_for_no_prs(self):
        from git_dev_metrics.metrics.calculator import calculate_reviews_given

        result = calculate_reviews_given([])
        assert result == {}

    def test_should_count_reviews_from_devs(self):
        from git_dev_metrics.metrics.calculator import calculate_reviews_given

        prs = [
            any_pr(
                id=1,
                number=1,
                user={"login": "alice"},
                reviews=[
                    {
                        "user": {"login": "bob"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T01:00:00Z",
                    },
                ],
            ),
            any_pr(
                id=2,
                number=2,
                user={"login": "bob"},
                reviews=[
                    {
                        "user": {"login": "alice"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T02:00:00Z",
                    },
                ],
            ),
        ]
        result = calculate_reviews_given(prs)
        assert result["alice"] == 1
        assert result["bob"] == 1

    def test_should_count_external_reviewers(self):
        from git_dev_metrics.metrics.calculator import calculate_reviews_given

        prs = [
            any_pr(
                id=1,
                number=1,
                user={"login": "alice"},
                reviews=[
                    {
                        "user": {"login": "external-reviewer"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T01:00:00Z",
                    },
                ],
            ),
        ]
        result = calculate_reviews_given(prs)
        assert result["external-reviewer"] == 1

    def test_should_count_each_pr_only_once_per_reviewer(self):
        # Arrange: bob submits 3 review events on alice's single PR
        from git_dev_metrics.metrics.calculator import calculate_reviews_given

        prs = [
            any_pr(
                id=1,
                number=1,
                user={"login": "alice"},
                reviews=[
                    {
                        "user": {"login": "bob"},
                        "state": "COMMENTED",
                        "submitted_at": "2024-01-01T01:00:00Z",
                    },
                    {
                        "user": {"login": "bob"},
                        "state": "CHANGES_REQUESTED",
                        "submitted_at": "2024-01-01T02:00:00Z",
                    },
                    {
                        "user": {"login": "bob"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T03:00:00Z",
                    },
                ],
            ),
        ]

        # Act
        result = calculate_reviews_given(prs)

        # Assert
        assert result["bob"] == 1

    def test_should_exclude_self_reviews(self):
        # Arrange: alice reviews her own PR
        from git_dev_metrics.metrics.calculator import calculate_reviews_given

        prs = [
            any_pr(
                id=1,
                number=1,
                user={"login": "alice"},
                reviews=[
                    {
                        "user": {"login": "alice"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T01:00:00Z",
                    },
                ],
            ),
        ]

        # Act
        result = calculate_reviews_given(prs)

        # Assert
        assert "alice" not in result

    def test_should_exclude_bot_suffix_reviewers(self):
        # Arrange
        from git_dev_metrics.metrics.calculator import calculate_reviews_given

        prs = [
            any_pr(
                id=1,
                number=1,
                user={"login": "alice"},
                reviews=[
                    {
                        "user": {"login": "patches-bot"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T01:00:00Z",
                    },
                ],
            )
        ]

        # Act
        result = calculate_reviews_given(prs)

        # Assert
        assert "patches-bot" not in result

    def test_should_not_collide_across_repos_with_same_pr_number(self):
        # Arrange: two PRs both numbered 1 from different repos with different reviews
        from git_dev_metrics.metrics.calculator import (
            calculate_pickup_time,
            calculate_reviews_given,
        )

        prs = [
            any_pr(
                id=10,
                number=1,
                user={"login": "alice"},
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-02T00:00:00Z",
                reviews=[
                    {
                        "user": {"login": "bob"},
                        "state": "APPROVED",
                        "submitted_at": "2024-01-01T02:00:00Z",
                    }
                ],
            ),
            any_pr(
                id=20,
                number=1,
                user={"login": "carol"},
                created_at="2024-02-01T00:00:00Z",
                merged_at="2024-02-02T00:00:00Z",
                reviews=[
                    {
                        "user": {"login": "dave"},
                        "state": "APPROVED",
                        "submitted_at": "2024-02-01T05:00:00Z",
                    }
                ],
            ),
        ]

        # Act
        reviews_given = calculate_reviews_given(prs)
        pickup = calculate_pickup_time(prs)

        # Assert: each reviewer counted once; pickup is per-PR (median of 2h and 5h = 3.5h)
        assert reviews_given["bob"] == 1
        assert reviews_given["dave"] == 1
        assert pickup == 3.5


class TestIsBotLogin:
    def test_should_match_known_bot(self):
        from git_dev_metrics.constants import is_bot_login

        assert is_bot_login("dependabot") is True

    def test_should_match_dash_bot_suffix(self):
        from git_dev_metrics.constants import is_bot_login

        assert is_bot_login("patches-bot") is True

    def test_should_match_bracket_bot_suffix(self):
        from git_dev_metrics.constants import is_bot_login

        assert is_bot_login("custom[bot]") is True

    def test_should_not_match_human_login(self):
        from git_dev_metrics.constants import is_bot_login

        assert is_bot_login("alice") is False

    def test_should_handle_none(self):
        from git_dev_metrics.constants import is_bot_login

        assert is_bot_login(None) is False


class TestGroupPrsByDevsBotExclusion:
    def test_should_exclude_dash_bot_authors(self):
        from git_dev_metrics.metrics.calculator import group_prs_by_devs

        prs = [
            any_pr(id=1, number=1, user={"login": "alice"}),
            any_pr(id=2, number=2, user={"login": "patches-bot"}),
        ]
        result = group_prs_by_devs(prs)
        assert "alice" in result
        assert "patches-bot" not in result


class TestGetStalePrs:
    """Test cases for get_stale_prs function."""

    def test_should_return_empty_for_empty_list(self):
        from git_dev_metrics.metrics.calculator import get_stale_prs

        result = get_stale_prs([], "myrepo")
        assert result == []

    def test_should_return_fresh_prs(self):
        from datetime import UTC, datetime, timedelta

        from git_dev_metrics.metrics.calculator import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "Fresh PR",
                    "created_at": (now - timedelta(days=1)).isoformat(),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert result == []

    def test_should_identify_stale_prs(self):
        from datetime import UTC, datetime, timedelta

        from git_dev_metrics.metrics.calculator import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "Stale PR",
                    "created_at": (now - timedelta(days=10)).isoformat(),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert len(result) == 1
        assert result[0]["number"] == 1
        assert result[0]["author"] == "alice"
        assert result[0]["repo"] == "myrepo"
        assert result[0]["age_hours"] > 24 * 7  # More than 7 days

    def test_should_sort_by_age_oldest_first(self):
        from datetime import UTC, datetime, timedelta

        from git_dev_metrics.metrics.calculator import get_stale_prs

        now = datetime.now(UTC)
        prs = cast(
            list[OpenPullRequest],
            [
                {
                    "number": 1,
                    "title": "Newer stale",
                    "created_at": (now - timedelta(days=8)).isoformat(),
                    "merged_at": None,
                    "user": {"login": "alice"},
                },
                {
                    "number": 2,
                    "title": "Older stale",
                    "created_at": (now - timedelta(days=15)).isoformat(),
                    "merged_at": None,
                    "user": {"login": "bob"},
                },
            ],
        )
        result = get_stale_prs(prs, "myrepo", lambda: now)
        assert result[0]["number"] == 2  # Older first
        assert result[1]["number"] == 1
        assert result[0]["repo"] == "myrepo"


class TestIsAiCoauthored:
    """Test cases for is_ai_coauthored function."""

    def test_should_return_false_for_none_body(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body=None))
        assert result is False

    def test_should_return_false_for_empty_body(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body=""))
        assert result is False

    def test_should_return_false_for_no_trailer(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body="This is a regular PR description"))
        assert result is False

    def test_should_return_true_for_coauthored_by_in_body(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body="Co-Authored-By: GitHub <noreply@github.com>"))
        assert result is True

    def test_should_be_case_insensitive(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body="co-authored-by: someone@example.com"))
        assert result is True

    def test_should_return_true_when_trailer_only_in_commit_message(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        pr = any_pr(
            body=None,
            commit_messages=["Fix bug\n\nCo-Authored-By: Claude <noreply@anthropic.com>"],
        )
        result = is_ai_coauthored(pr)
        assert result is True

    def test_should_return_true_when_trailer_in_one_of_many_commits(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        pr = any_pr(
            body="Regular PR",
            commit_messages=[
                "Refactor module",
                "Add tests",
                "Polish\n\n🤖 Generated with Claude Code",
            ],
        )
        result = is_ai_coauthored(pr)
        assert result is True

    def test_should_return_false_when_no_trailer_in_body_or_commits(self):
        from git_dev_metrics.metrics.calculator import is_ai_coauthored

        pr = any_pr(
            body="Regular PR",
            commit_messages=["Refactor module", "Add tests"],
        )
        result = is_ai_coauthored(pr)
        assert result is False


class TestCalculateAiPercentage:
    """Test cases for calculate_ai_percentage function."""

    def test_should_return_zero_for_empty_list(self):
        from git_dev_metrics.metrics.calculator import calculate_ai_percentage

        result = calculate_ai_percentage([])
        assert result == 0.0

    def test_should_return_zero_for_no_ai_prs(self):
        from git_dev_metrics.metrics.calculator import calculate_ai_percentage

        prs = [
            any_pr(body=None),
            any_pr(body="Regular PR"),
            any_pr(body=None),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 0.0

    def test_should_calculate_percentage_correctly(self):
        from git_dev_metrics.metrics.calculator import calculate_ai_percentage

        prs = [
            any_pr(body="Co-Authored-By: someone@example.com"),
            any_pr(body="Regular PR"),
            any_pr(body="Co-Authored-By: another@example.com"),
            any_pr(body="Another regular PR"),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 50.0

    def test_should_handle_all_ai_prs(self):
        from git_dev_metrics.metrics.calculator import calculate_ai_percentage

        prs = [
            any_pr(body="Co-Authored-By: someone@example.com"),
            any_pr(body="Co-Authored-By: another@example.com"),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 100.0

    def test_should_round_to_one_decimal(self):
        from git_dev_metrics.metrics.calculator import calculate_ai_percentage

        prs = [
            any_pr(body="Co-Authored-By: someone@example.com"),
            any_pr(body="Regular PR"),
            any_pr(body="Regular PR"),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 33.3

    def test_should_count_pr_with_trailer_only_in_commit_message(self):
        from git_dev_metrics.metrics.calculator import calculate_ai_percentage

        prs = [
            any_pr(body="Regular PR", commit_messages=["Co-Authored-By: Claude"]),
            any_pr(body="Regular PR", commit_messages=["Refactor"]),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 50.0


class TestBuildSummary:
    """Test cases for build_summary reading team_metrics."""

    def test_should_read_team_metrics_directly(self):
        from git_dev_metrics.metrics.printer.html_printer import build_summary

        metrics = {
            "dev_metrics": {},
            "repo_metrics": {},
            "team_metrics": {
                "pr_count": 658,
                "cycle_time": 8.4,
                "pickup_time": 5.3,
                "reviews_given": 967,
                "ai_percentage": 80.4,
                "avg_lines_per_pr": 742.0,
            },
        }
        result = build_summary(metrics)

        assert result["total_prs"] == 658
        assert result["median_cycle"] == 8.4
        assert result["median_pickup"] == 5.3
        assert result["total_reviews"] == 967
        assert result["ai_adoption"] == 80
        assert result["avg_lines_per_pr"] == 742.0

    def test_should_zero_out_when_team_metrics_missing(self):
        from git_dev_metrics.metrics.printer.html_printer import build_summary

        result = build_summary({"dev_metrics": {}, "repo_metrics": {}})

        assert result["total_prs"] == 0
        assert result["median_cycle"] == 0
        assert result["median_pickup"] == 0
        assert result["ai_adoption"] == 0
        assert result["avg_lines_per_pr"] == 0
        assert result["review_ratio"] == 0.0
        assert result["top_reviewer"] == ""
        assert result["max_review_share"] == 0

    def test_should_compute_review_ratio_from_team_totals(self):
        from git_dev_metrics.metrics.printer.html_printer import build_summary

        metrics = {
            "dev_metrics": {"alice": {"reviews_given": 4}, "bob": {"reviews_given": 6}},
            "team_metrics": {"pr_count": 5, "reviews_given": 10},
        }
        result = build_summary(metrics)

        assert result["review_ratio"] == 2.0

    def test_should_pick_top_reviewer_and_share(self):
        from git_dev_metrics.metrics.printer.html_printer import build_summary

        metrics = {
            "dev_metrics": {
                "alice": {"reviews_given": 3},
                "bob": {"reviews_given": 7},
            },
            "team_metrics": {"pr_count": 5, "reviews_given": 10},
        }
        result = build_summary(metrics)

        assert result["top_reviewer"] == "bob"
        assert result["max_review_share"] == 70

    def test_should_break_top_reviewer_ties_alphabetically(self):
        from git_dev_metrics.metrics.printer.html_printer import build_summary

        metrics = {
            "dev_metrics": {
                "carol": {"reviews_given": 5},
                "alice": {"reviews_given": 5},
                "bob": {"reviews_given": 5},
            },
            "team_metrics": {"pr_count": 5, "reviews_given": 15},
        }
        result = build_summary(metrics)

        assert result["top_reviewer"] == "alice"
        assert result["max_review_share"] == 33

    def test_should_zero_review_culture_when_no_reviews(self):
        from git_dev_metrics.metrics.printer.html_printer import build_summary

        metrics = {
            "dev_metrics": {"alice": {"reviews_given": 0}},
            "team_metrics": {"pr_count": 4, "reviews_given": 0},
        }
        result = build_summary(metrics)

        assert result["review_ratio"] == 0.0
        assert result["top_reviewer"] == ""
        assert result["max_review_share"] == 0

    def test_should_zero_review_ratio_when_no_prs(self):
        from git_dev_metrics.metrics.printer.html_printer import build_summary

        metrics = {
            "dev_metrics": {"alice": {"reviews_given": 2}},
            "team_metrics": {"pr_count": 0, "reviews_given": 2},
        }
        result = build_summary(metrics)

        assert result["review_ratio"] == 0.0

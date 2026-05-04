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
        prs = []
        result = calculate_pickup_time(prs, {})
        assert result == 0.0

    def test_should_return_zero_when_no_reviews(self):
        prs = [
            any_pr(number=1, created_at="2024-01-01T00:00:00Z", merged_at="2024-01-02T00:00:00Z")
        ]
        result = calculate_pickup_time(prs, {1: []})
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(number=1, created_at="2024-01-01T00:00:00Z", merged_at="2024-01-02T00:00:00Z")
        ]
        reviews = {
            1: [
                {
                    "user": {"login": "reviewer"},
                    "state": "COMMENTED",
                    "submitted_at": "2024-01-01T12:00:00Z",
                }
            ]
        }
        result = calculate_pickup_time(prs, reviews)
        assert result == 0.0

    def test_should_calculate_pickup_time(self):
        prs = [
            any_pr(number=1, created_at="2024-01-01T00:00:00Z", merged_at="2024-01-02T00:00:00Z")
        ]
        reviews = {
            1: [
                {
                    "user": {"login": "reviewer"},
                    "state": "APPROVED",
                    "submitted_at": "2024-01-01T12:00:00Z",
                }
            ]
        }
        result = calculate_pickup_time(prs, reviews)
        assert result == 12.0


class TestCalculateReviewTime:
    """Test cases for calculate_review_time function."""

    def test_should_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_review_time(prs, {})
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(number=1, created_at="2024-01-01T00:00:00Z", merged_at="2024-01-02T00:00:00Z")
        ]
        reviews = {
            1: [
                {
                    "user": {"login": "reviewer"},
                    "state": "COMMENTED",
                    "submitted_at": "2024-01-01T12:00:00Z",
                }
            ]
        }
        result = calculate_review_time(prs, reviews)
        assert result == 0.0

    def test_should_calculate_review_time(self):
        prs = [
            any_pr(number=1, created_at="2024-01-01T00:00:00Z", merged_at="2024-01-03T00:00:00Z")
        ]
        reviews = {
            1: [
                {
                    "user": {"login": "reviewer"},
                    "state": "APPROVED",
                    "submitted_at": "2024-01-02T00:00:00Z",
                }
            ]
        }
        result = calculate_review_time(prs, reviews)
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


class TestCalculateReviewsGiven:
    """Test cases for calculate_reviews_given function."""

    def test_should_return_zero_for_no_reviews(self):
        from git_dev_metrics.metrics.calculator import calculate_reviews_given

        devs = {"alice": [], "bob": []}
        reviews = {1: [], 2: []}
        result = calculate_reviews_given(reviews, devs)
        assert result == {"alice": 0, "bob": 0}

    def test_should_count_reviews_from_devs(self):
        from git_dev_metrics.metrics.calculator import calculate_reviews_given, group_prs_by_devs

        prs = [
            any_pr(id=1, number=1, user={"login": "alice"}),
            any_pr(id=2, number=2, user={"login": "bob"}),
        ]
        devs = group_prs_by_devs(prs)
        reviews = {
            1: [
                {
                    "user": {"login": "bob"},
                    "state": "APPROVED",
                    "submitted_at": "2024-01-01T01:00:00Z",
                },
            ],
            2: [
                {
                    "user": {"login": "alice"},
                    "state": "APPROVED",
                    "submitted_at": "2024-01-01T02:00:00Z",
                },
            ],
        }
        result = calculate_reviews_given(reviews, devs)
        assert result["alice"] == 1
        assert result["bob"] == 1

    def test_should_include_reviewers_not_in_devs(self):
        from git_dev_metrics.metrics.calculator import calculate_reviews_given, group_prs_by_devs

        prs = [
            any_pr(id=1, number=1, user={"login": "alice"}),
        ]
        devs = group_prs_by_devs(prs)
        reviews = {
            1: [
                {
                    "user": {"login": "external-reviewer"},
                    "state": "APPROVED",
                    "submitted_at": "2024-01-01T01:00:00Z",
                },
            ],
        }
        result = calculate_reviews_given(reviews, devs)
        assert result["alice"] == 0
        assert result["external-reviewer"] == 1

    def test_should_count_each_pr_only_once_per_reviewer(self):
        # Arrange: bob submits 3 review events on alice's single PR
        from git_dev_metrics.metrics.calculator import calculate_reviews_given, group_prs_by_devs

        prs = [
            any_pr(id=1, number=1, user={"login": "alice"}),
        ]
        devs = group_prs_by_devs(prs)
        reviews = {
            1: [
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
        }

        # Act
        result = calculate_reviews_given(reviews, devs)

        # Assert
        assert result["bob"] == 1

    def test_should_exclude_self_reviews(self):
        # Arrange: alice reviews her own PR
        from git_dev_metrics.metrics.calculator import calculate_reviews_given, group_prs_by_devs

        prs = [
            any_pr(id=1, number=1, user={"login": "alice"}),
        ]
        devs = group_prs_by_devs(prs)
        reviews = {
            1: [
                {
                    "user": {"login": "alice"},
                    "state": "APPROVED",
                    "submitted_at": "2024-01-01T01:00:00Z",
                },
            ],
        }

        # Act
        result = calculate_reviews_given(reviews, devs)

        # Assert
        assert result["alice"] == 0

    def test_should_exclude_bot_suffix_reviewers(self):
        # Arrange
        from git_dev_metrics.metrics.calculator import calculate_reviews_given, group_prs_by_devs

        prs = [any_pr(id=1, number=1, user={"login": "alice"})]
        devs = group_prs_by_devs(prs)
        reviews = {
            1: [
                {
                    "user": {"login": "patches-bot"},
                    "state": "APPROVED",
                    "submitted_at": "2024-01-01T01:00:00Z",
                },
            ],
        }

        # Act
        result = calculate_reviews_given(reviews, devs)

        # Assert
        assert "patches-bot" not in result


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


class TestGroupPrsByLabels:
    """Test cases for group_prs_by_labels function."""

    def test_should_return_empty_dict_for_empty_list(self):
        from git_dev_metrics.metrics.calculator import group_prs_by_labels

        result = group_prs_by_labels([])
        assert result == {}

    def test_should_group_prs_by_label(self):
        from git_dev_metrics.metrics.calculator import group_prs_by_labels

        prs = [
            any_pr(labels=["bug"]),
            any_pr(labels=["feature"]),
            any_pr(labels=["bug"]),
        ]
        result = group_prs_by_labels(prs)
        assert len(result["bug"]) == 2
        assert len(result["feature"]) == 1

    def test_should_handle_pr_with_multiple_labels(self):
        from git_dev_metrics.metrics.calculator import group_prs_by_labels

        prs = [any_pr(labels=["bug", "urgent"])]
        result = group_prs_by_labels(prs)
        assert len(result["bug"]) == 1
        assert len(result["urgent"]) == 1

    def test_should_group_prs_without_labels_under_no_label(self):
        from git_dev_metrics.metrics.calculator import group_prs_by_labels

        prs = [
            any_pr(labels=[]),
            any_pr(labels=["bug"]),
        ]
        result = group_prs_by_labels(prs)
        assert len(result["(no label)"]) == 1
        assert len(result["bug"]) == 1

    def test_should_default_to_empty_list_for_missing_labels_field(self):
        from git_dev_metrics.metrics.calculator import group_prs_by_labels

        prs = [any_pr(labels=[])]
        result = group_prs_by_labels(prs)
        assert "(no label)" in result

    def test_should_default_to_30_for_invalid(self):
        assert _parse_period_days("invalid") == 30


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

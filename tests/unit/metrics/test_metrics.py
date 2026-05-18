"""Unit tests for reports.py functions."""

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
from git_dev_metrics.utils import TimePeriod
from git_dev_metrics.utils import period_days as _period_days

from ..conftest import any_pr, approved_review, dt


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
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            )
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_return_average_cycle_time_for_multiple_prs(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            ),
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 36.0

    def test_should_handle_prs_with_different_time_zones(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=12, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=12, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=18, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_use_first_commit_when_older_than_created_at(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                first_commit_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=2, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_use_created_at_when_older_than_first_commit(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                first_commit_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=2, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_use_created_at_when_first_commit_is_none(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                first_commit_at=None,
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_exclude_draft_window_using_ready_for_review_at(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                ready_for_review_at=dt(year=2024, month=1, day=4, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=5, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=4, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_ignore_ready_for_review_when_before_start_time(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                first_commit_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                ready_for_review_at=dt(year=2023, month=12, day=31, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=2, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_skip_prs_without_approval(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 0.0


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
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "COMMENTED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=12, minute=0),
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
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "APPROVED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=12, minute=0),
                    }
                ],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 12.0

    def test_should_exclude_draft_window_from_pickup(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                ready_for_review_at=dt(year=2024, month=1, day=4, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=5, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=4, hour=6, minute=0))],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 6.0


class TestCalculateReviewTime:
    """Test cases for calculate_review_time function."""

    def test_should_return_zero_when_no_prs_provided(self):
        result = calculate_review_time([])
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "COMMENTED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=12, minute=0),
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
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "APPROVED",
                        "submitted_at": dt(year=2024, month=1, day=2, hour=0, minute=0),
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


class TestPeriodDays:
    """Test cases for _period_days function — derives whole days from a TimePeriod.

    This is the source of truth for the prs_per_week denominator. Must reflect the
    real span (28/29/30/31) for calendar months, not the period-string shape.
    """

    def test_should_return_28_for_february_non_leap(self):
        period = TimePeriod(
            since=dt(year=2026, month=2, day=1),
            until=dt(year=2026, month=3, day=1),
        )

        assert _period_days(period) == 28

    def test_should_return_29_for_february_leap(self):
        period = TimePeriod(
            since=dt(year=2024, month=2, day=1),
            until=dt(year=2024, month=3, day=1),
        )

        assert _period_days(period) == 29

    def test_should_return_31_for_thirty_one_day_month(self):
        period = TimePeriod(
            since=dt(year=2026, month=3, day=1),
            until=dt(year=2026, month=4, day=1),
        )

        assert _period_days(period) == 31

    def test_should_return_exact_days_for_sliding_window(self):
        until = dt(year=2026, month=5, day=8, hour=12, minute=0)
        since = dt(year=2026, month=4, day=8, hour=12, minute=0)
        period = TimePeriod(since=since, until=until)

        assert _period_days(period) == 30

    def test_should_clamp_to_one_for_zero_span(self):
        instant = dt(year=2026, month=5, day=8)
        period = TimePeriod(since=instant, until=instant)

        assert _period_days(period) == 1


class TestCalculatePrsPerWeekUsesActualSpan:
    """Regression: prs_per_week was computed with hard-coded 30 for `last_month` and YYYY-MM."""

    def test_should_match_calendar_month_length_for_february(self):
        period = TimePeriod(
            since=dt(year=2026, month=2, day=1),
            until=dt(year=2026, month=3, day=1),
        )
        prs = [any_pr(id=i, number=i) for i in range(1, 5)]

        result = calculate_prs_per_week(prs, _period_days(period))

        # 4 PRs over 28d = 1.0/wk; old 30d default would give ≈ 0.93
        assert result == 1.0


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
                        "submitted_at": dt(year=2024, month=1, day=1, hour=1, minute=0),
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
                        "submitted_at": dt(year=2024, month=1, day=1, hour=2, minute=0),
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
                        "submitted_at": dt(year=2024, month=1, day=1, hour=1, minute=0),
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
                        "submitted_at": dt(year=2024, month=1, day=1, hour=1, minute=0),
                    },
                    {
                        "user": {"login": "bob"},
                        "state": "CHANGES_REQUESTED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=2, minute=0),
                    },
                    {
                        "user": {"login": "bob"},
                        "state": "APPROVED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=3, minute=0),
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
                        "submitted_at": dt(year=2024, month=1, day=1, hour=1, minute=0),
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
                        "submitted_at": dt(year=2024, month=1, day=1, hour=1, minute=0),
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
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "bob"},
                        "state": "APPROVED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=2, minute=0),
                    }
                ],
            ),
            any_pr(
                id=20,
                number=1,
                user={"login": "carol"},
                created_at=dt(year=2024, month=2, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=2, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "dave"},
                        "state": "APPROVED",
                        "submitted_at": dt(year=2024, month=2, day=1, hour=5, minute=0),
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

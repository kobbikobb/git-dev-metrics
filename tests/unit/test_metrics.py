"""Unit tests for reports.py functions."""

from git_dev_metrics.metrics import (
    calculate_cycle_time,
    calculate_pickup_time,
    calculate_pr_size,
    calculate_prs_per_week,
    calculate_review_time,
    calculate_throughput,
    median,
)
from git_dev_metrics.metrics.analyzer import _parse_period_days

from .conftest import any_open_pr, any_pr


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

    def test_should_default_to_30_for_invalid(self):
        assert _parse_period_days("invalid") == 30


class TestCalculatePrAging:
    """Test cases for calculate_pr_aging function."""

    def test_should_return_zeros_for_empty_list(self):
        from git_dev_metrics.metrics.calculator import calculate_pr_aging

        result = calculate_pr_aging([])
        assert result["open_count"] == 0
        assert result["stale_count"] == 0
        assert result["avg_age_hours"] == 0.0
        assert result["oldest_pr_age_hours"] == 0.0

    def test_should_calculate_aging_for_fresh_prs(self):
        from datetime import datetime, timezone, timedelta
        from git_dev_metrics.metrics.calculator import calculate_pr_aging

        now = datetime.now(timezone.utc)
        recent = now - timedelta(hours=2)

        prs = [any_open_pr(created_at=recent)]
        result = calculate_pr_aging(prs)

        assert result["open_count"] == 1
        assert result["stale_count"] == 0
        assert 1.5 < result["avg_age_hours"] < 2.5

    def test_should_identify_stale_prs(self):
        from datetime import datetime, timezone, timedelta
        from git_dev_metrics.metrics.calculator import calculate_pr_aging

        now = datetime.now(timezone.utc)
        stale = now - timedelta(days=10)

        prs = [any_open_pr(created_at=stale)]
        result = calculate_pr_aging(prs)

        assert result["open_count"] == 1
        assert result["stale_count"] == 1
        assert result["oldest_pr_age_hours"] > 24 * 7  # > 7 days


class TestIdentifyBottlenecks:
    """Test cases for identify_bottlenecks function."""

    def test_should_return_empty_for_no_prs(self):
        from git_dev_metrics.metrics.calculator import identify_bottlenecks

        result = identify_bottlenecks([])
        assert result["stale_prs"] == []
        assert result["waiting_for_review"] == []
        assert result["overwhelmed_reviewers"] == []

    def test_should_identify_stale_prs(self):
        from datetime import datetime, timezone, timedelta
        from git_dev_metrics.metrics.calculator import identify_bottlenecks

        now = datetime.now(timezone.utc)
        stale = now - timedelta(days=10)

        prs = [
            any_open_pr(
                number=123,
                title="Stale PR",
                user={"login": "alice"},
                created_at=stale,
            )
        ]
        result = identify_bottlenecks(prs)

        assert len(result["stale_prs"]) == 1
        assert result["stale_prs"][0]["number"] == 123

    def test_should_identify_overwhelmed_reviewers(self):
        from git_dev_metrics.metrics.calculator import identify_bottlenecks

        prs = [
            any_open_pr(
                number=1,
                user={"login": "alice"},
                requested_reviewers=[
                    {"login": "bob"},
                    {"login": "bob"},
                    {"login": "bob"},
                    {"login": "bob"},
                    {"login": "bob"},
                    {"login": "bob"},
                ],
            )
        ]
        result = identify_bottlenecks(prs)

        assert len(result["overwhelmed_reviewers"]) == 1
        assert result["overwhelmed_reviewers"][0]["reviewer"] == "bob"
        assert result["overwhelmed_reviewers"][0]["pending_count"] == 6

    def test_should_limit_results_to_10(self):
        from datetime import datetime, timezone, timedelta
        from git_dev_metrics.metrics.calculator import identify_bottlenecks

        now = datetime.now(timezone.utc)
        recent = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        prs = [
            any_open_pr(
                number=i,
                user={"login": f"dev{i}"},
                created_at=recent,
                requested_reviewers=[{"login": "reviewer"}],
            )
            for i in range(15)
        ]
        result = identify_bottlenecks(prs)

        assert len(result["overwhelmed_reviewers"]) == 1
        assert len(result["stale_prs"]) == 0

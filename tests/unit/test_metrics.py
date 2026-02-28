"""Unit tests for reports.py functions."""

from git_dev_metrics.metrics import (
    calculate_cycle_time,
    calculate_pr_size,
    calculate_pickup_time,
    calculate_review_time,
    calculate_prs_per_week,
    calculate_throughput,
    median,
)
from git_dev_metrics.metrics.analyzer import _parse_period_days

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

    def test_should_default_to_30_for_invalid(self):
        assert _parse_period_days("invalid") == 30

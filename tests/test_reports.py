"""Unit tests for reports.py functions."""

from datetime import datetime, timedelta
import pytest
from git_dev_metrics.reports import (
    parse_time_period,
    calculate_cycle_time,
    calculate_pr_size,
    calculate_throughput,
    PullRequest,
)


class TestParseTimePeriod:
    """Test cases for parse_time_period function."""

    def test_should_return_one_day_ago_for_1d_period(self):
        # Arrange
        event_period = "1d"
        expected = datetime.now() - timedelta(days=1)

        # Act
        result = parse_time_period(event_period)

        # Assert
        assert abs((result - expected).total_seconds()) < 60

    def test_should_return_seven_days_ago_for_7d_period(self):
        # Arrange
        event_period = "7d"
        expected = datetime.now() - timedelta(days=7)

        # Act
        result = parse_time_period(event_period)

        # Assert
        assert abs((result - expected).total_seconds()) < 60

    def test_should_return_thirty_days_ago_for_30d_period(self):
        # Arrange
        event_period = "30d"
        expected = datetime.now() - timedelta(days=30)

        # Act
        result = parse_time_period(event_period)

        # Assert
        assert abs((result - expected).total_seconds()) < 60

    def test_should_return_ninety_days_ago_for_90d_period(self):
        # Arrange
        event_period = "90d"
        expected = datetime.now() - timedelta(days=90)

        # Act
        result = parse_time_period(event_period)

        # Assert
        assert abs((result - expected).total_seconds()) < 60

    def test_should_return_thirty_days_ago_for_invalid_period(self):
        # Arrange
        event_period = "invalid"
        expected = datetime.now() - timedelta(days=30)

        # Act
        result = parse_time_period(event_period)

        # Assert
        assert abs((result - expected).total_seconds()) < 60


class TestCalculateCycleTime:
    """Test cases for calculate_cycle_time function."""

    def test_should_return_zero_when_no_prs_provided(self):
        # Arrange
        prs = []

        # Act
        result = calculate_cycle_time(prs)

        # Assert
        assert result == 0.0

    def test_should_return_correct_cycle_time_for_single_pr(self):
        # Arrange
        prs = [
            {"created_at": "2024-01-01T00:00:00Z", "merged_at": "2024-01-02T00:00:00Z"}
        ]

        # Act
        result = calculate_cycle_time(prs)

        # Assert
        assert result == 1.0

    def test_should_return_average_cycle_time_for_multiple_prs(self):
        # Arrange
        prs = [
            {"created_at": "2024-01-01T00:00:00Z", "merged_at": "2024-01-02T00:00:00Z"},
            {"created_at": "2024-01-01T00:00:00Z", "merged_at": "2024-01-03T00:00:00Z"},
        ]

        # Act
        result = calculate_cycle_time(prs)

        # Assert
        assert result == 1.5

    def test_should_handle_prs_with_different_time_zones(self):
        # Arrange
        prs = [
            {"created_at": "2024-01-01T12:00:00Z", "merged_at": "2024-01-02T12:00:00Z"}
        ]

        # Act
        result = calculate_cycle_time(prs)

        # Assert
        assert result == 1.0


class TestCalculatePrSize:
    """Test cases for calculate_pr_size function."""

    def test_should_return_zero_when_no_prs_provided(self):
        # Arrange
        prs = []

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 0

    def test_should_return_correct_size_for_single_pr(self):
        # Arrange
        prs = [{"additions": 100, "deletions": 50}]

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 150

    def test_should_return_average_size_for_multiple_prs(self):
        # Arrange
        prs = [
            {"additions": 100, "deletions": 50},
            {"additions": 200, "deletions": 100},
        ]

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 225

    def test_should_handle_missing_additions_and_deletions(self):
        # Arrange
        prs = [{"additions": 100}, {"deletions": 50}, {}]

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 50


class TestCalculateThroughput:
    """Test cases for calculate_throughput function."""

    def test_should_return_zero_when_no_prs_provided(self):
        # Arrange
        prs = []

        # Act
        result = calculate_throughput(prs)

        # Assert
        assert result == 0

    def test_should_return_count_of_prs(self):
        # Arrange
        prs = [{"number": 1}, {"number": 2}, {"number": 3}]

        # Act
        result = calculate_throughput(prs)

        # Assert
        assert result == 3

    def test_should_handle_empty_pr_objects(self):
        # Arrange
        prs = [{}, {}, {}]

        # Act
        result = calculate_throughput(prs)

        # Assert
        assert result == 3

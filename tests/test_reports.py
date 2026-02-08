"""Unit tests for reports.py functions."""

from git_dev_metrics.reports import (
    calculate_cycle_time,
    calculate_pr_size,
    calculate_throughput,
)


class TestCalculateCycleTime:
    """Test cases for calculate_cycle_time function."""

    def test_return_zero_when_no_prs_provided(self):
        # Arrange
        prs = []

        # Act
        result = calculate_cycle_time(prs)

        # Assert
        assert result == 0.0

    def test_return_correct_cycle_time_for_single_pr(self):
        # Arrange
        prs = [
            {"created_at": "2024-01-01T00:00:00Z", "merged_at": "2024-01-02T00:00:00Z"}
        ]

        # Act
        result = calculate_cycle_time(prs)

        # Assert
        assert result == 1.0

    def test_return_average_cycle_time_for_multiple_prs(self):
        # Arrange
        prs = [
            {"created_at": "2024-01-01T00:00:00Z", "merged_at": "2024-01-02T00:00:00Z"},
            {"created_at": "2024-01-01T00:00:00Z", "merged_at": "2024-01-03T00:00:00Z"},
        ]

        # Act
        result = calculate_cycle_time(prs)

        # Assert
        assert result == 1.5

    def test_handle_prs_with_different_time_zones(self):
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

    def test_return_zero_when_no_prs_provided(self):
        # Arrange
        prs = []

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 0

    def test_return_correct_size_for_single_pr(self):
        # Arrange
        prs = [{"additions": 100, "deletions": 50}]

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 150

    def test_return_average_size_for_multiple_prs(self):
        # Arrange
        prs = [
            {"additions": 100, "deletions": 50},
            {"additions": 200, "deletions": 100},
        ]

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 225

    def test_handle_missing_additions_and_deletions(self):
        # Arrange
        prs = [{"additions": 100}, {"deletions": 50}, {}]

        # Act
        result = calculate_pr_size(prs)

        # Assert
        assert result == 50


class TestCalculateThroughput:
    """Test cases for calculate_throughput function."""

    def test_return_zero_when_no_prs_provided(self):
        # Arrange
        prs = []

        # Act
        result = calculate_throughput(prs)

        # Assert
        assert result == 0

    def test_return_count_of_prs(self):
        # Arrange
        prs = [{"number": 1}, {"number": 2}, {"number": 3}]

        # Act
        result = calculate_throughput(prs)

        # Assert
        assert result == 3

    def test_handle_empty_pr_objects(self):
        # Arrange
        prs = [{}, {}, {}]

        # Act
        result = calculate_throughput(prs)

        # Assert
        assert result == 3

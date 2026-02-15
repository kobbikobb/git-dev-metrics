"""Unit tests for date_utils.py functions."""

from datetime import UTC, datetime, timedelta

from git_dev_metrics.date_utils import parse_time_period

# freezgun was considered, brings in more complexity then it's worth


def is_same_date(date1: datetime, date2: datetime):
    return abs((date1 - date2).total_seconds()) < 1


class TestParseTimePeriod:
    """Test cases for parse_time_period function."""

    def test_should_return_one_day_ago_for_1d_period(self):
        event_period = "1d"
        expected = datetime.now(UTC) - timedelta(days=1)

        result = parse_time_period(event_period)

        assert is_same_date(result, expected)

    def test_should_return_seven_days_ago_for_7d_period(self):
        event_period = "7d"
        expected = datetime.now(UTC) - timedelta(days=7)

        result = parse_time_period(event_period)

        assert is_same_date(result, expected)

    def test_should_return_thirty_days_ago_for_30d_period(self):
        event_period = "30d"
        expected = datetime.now(UTC) - timedelta(days=30)

        result = parse_time_period(event_period)

        assert is_same_date(result, expected)

    def test_should_return_ninety_days_ago_for_90d_period(self):
        event_period = "90d"
        expected = datetime.now(UTC) - timedelta(days=90)

        result = parse_time_period(event_period)

        assert is_same_date(result, expected)

    def test_should_return_thirty_days_ago_for_invalid_period(self):
        event_period = "invalid"
        expected = datetime.now(UTC) - timedelta(days=30)

        result = parse_time_period(event_period)

        assert is_same_date(result, expected)

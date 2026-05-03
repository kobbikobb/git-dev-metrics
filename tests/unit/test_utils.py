"""Unit tests for date_utils.py functions."""

from datetime import UTC, datetime, timedelta

from git_dev_metrics.utils import get_period_display_name, parse_time_period

# freezgun was considered, brings in more complexity then it's worth


def is_same_date(date1: datetime, date2: datetime):
    return abs((date1 - date2).total_seconds()) < 1


class TestParseTimePeriod:
    """Test cases for parse_time_period function."""

    def test_should_return_one_day_ago_for_1d_period(self):
        event_period = "1d"
        expected_start = datetime.now(UTC) - timedelta(days=1)
        expected_end = datetime.now(UTC)

        start, end = parse_time_period(event_period)

        assert is_same_date(start, expected_start)
        assert is_same_date(end, expected_end)

    def test_should_return_seven_days_ago_for_7d_period(self):
        event_period = "7d"
        expected_start = datetime.now(UTC) - timedelta(days=7)
        expected_end = datetime.now(UTC)

        start, end = parse_time_period(event_period)

        assert is_same_date(start, expected_start)
        assert is_same_date(end, expected_end)

    def test_should_return_thirty_days_ago_for_30d_period(self):
        event_period = "30d"
        expected_start = datetime.now(UTC) - timedelta(days=30)
        expected_end = datetime.now(UTC)

        start, end = parse_time_period(event_period)

        assert is_same_date(start, expected_start)
        assert is_same_date(end, expected_end)

    def test_should_return_ninety_days_ago_for_90d_period(self):
        event_period = "90d"
        expected_start = datetime.now(UTC) - timedelta(days=90)
        expected_end = datetime.now(UTC)

        start, end = parse_time_period(event_period)

        assert is_same_date(start, expected_start)
        assert is_same_date(end, expected_end)

    def test_should_return_thirty_days_ago_for_invalid_period(self):
        event_period = "invalid"
        expected_start = datetime.now(UTC) - timedelta(days=30)
        expected_end = datetime.now(UTC)

        start, end = parse_time_period(event_period)

        assert is_same_date(start, expected_start)
        assert is_same_date(end, expected_end)

    def test_should_return_last_calendar_month_range_for_1m(self):
        event_period = "1m"
        today = datetime.now(UTC)
        first_of_current = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_prev_month = first_of_current - timedelta(days=1)
        expected_start = last_day_prev_month.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        expected_end = last_day_prev_month.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        start, end = parse_time_period(event_period)

        assert is_same_date(start, expected_start)
        assert is_same_date(end, expected_end)


class TestGetPeriodDisplayName:
    """Test cases for get_period_display_name function."""

    def test_should_return_month_name_for_1m(self):
        today = datetime.now(UTC)
        first_of_current = today.replace(day=1)
        last_day_prev = first_of_current - timedelta(days=1)
        expected = last_day_prev.strftime("%B %Y")

        result = get_period_display_name("1m")

        assert result == expected

    def test_should_return_last_period_for_other_values(self):
        assert get_period_display_name("30d") == "Last 30d"
        assert get_period_display_name("7d") == "Last 7d"
        assert get_period_display_name("90d") == "Last 90d"

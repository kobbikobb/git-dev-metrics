"""Unit tests for date_utils.py functions."""

from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time

from git_dev_metrics.utils import TimePeriod, get_last_month, parse_time_period


class TestTimePeriod:
    def test_should_construct_when_since_before_until(self):
        since = datetime(2024, 1, 1, tzinfo=UTC)
        until = datetime(2024, 2, 1, tzinfo=UTC)

        period = TimePeriod(since=since, until=until)

        assert period.since == since
        assert period.until == until

    def test_should_raise_when_since_after_until(self):
        since = datetime(2024, 2, 1, tzinfo=UTC)
        until = datetime(2024, 1, 1, tzinfo=UTC)

        with pytest.raises(ValueError, match="since must be before until"):
            TimePeriod(since=since, until=until)


class TestParseTimePeriod:
    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_one_day_period_for_1d(self):
        result = parse_time_period("1d")

        assert result.until == datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        assert result.since == datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC) - timedelta(days=1)

    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_seven_day_period_for_7d(self):
        result = parse_time_period("7d")

        assert result.until - result.since == timedelta(days=7)

    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_thirty_day_period_for_30d(self):
        result = parse_time_period("30d")

        assert result.until - result.since == timedelta(days=30)

    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_ninety_day_period_for_90d(self):
        result = parse_time_period("90d")

        assert result.until - result.since == timedelta(days=90)

    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_one_eighty_day_period_for_180d(self):
        result = parse_time_period("180d")

        assert result.until - result.since == timedelta(days=180)

    def test_should_raise_for_invalid_period(self):
        with pytest.raises(ValueError, match="Unsupported period"):
            parse_time_period("invalid")

    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_last_month_for_last_month(self):
        result = parse_time_period("last_month")

        expected = get_last_month()
        assert result.since == expected.since
        assert result.until == expected.until


class TestGetLastMonth:
    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_last_month_range_mid_month(self):
        result = get_last_month()

        assert result.since == datetime(2024, 5, 1, tzinfo=UTC)
        assert result.until == datetime(2024, 6, 1, tzinfo=UTC)

    @freeze_time("2024-01-15 12:00:00")
    def test_should_cross_year_boundary(self):
        result = get_last_month()

        assert result.since == datetime(2023, 12, 1, tzinfo=UTC)
        assert result.until == datetime(2024, 1, 1, tzinfo=UTC)

    @freeze_time("2024-03-01 00:00:00")
    def test_should_handle_first_of_month(self):
        result = get_last_month()

        assert result.since == datetime(2024, 2, 1, tzinfo=UTC)
        assert result.until == datetime(2024, 3, 1, tzinfo=UTC)

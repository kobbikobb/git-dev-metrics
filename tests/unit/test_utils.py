"""Unit tests for date_utils.py functions."""

from datetime import timedelta

import pytest
from freezegun import freeze_time

from git_dev_metrics.utils import TimePeriod, get_last_month, parse_time_period
from git_dev_metrics.utils.date_utils import month_range

from .conftest import dt


class TestTimePeriod:
    def test_should_construct_when_since_before_until(self):
        since = dt(year=2024, month=1, day=1)
        until = dt(year=2024, month=2, day=1)

        period = TimePeriod(since=since, until=until)

        assert period.since == since
        assert period.until == until

    def test_should_raise_when_since_after_until(self):
        since = dt(year=2024, month=2, day=1)
        until = dt(year=2024, month=1, day=1)

        with pytest.raises(ValueError, match="since must be before until"):
            TimePeriod(since=since, until=until)


class TestParseTimePeriod:
    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_one_day_period_for_1d(self):
        result = parse_time_period("1d")

        assert result.until == dt(year=2024, month=6, day=15, hour=12, minute=0, second=0)
        assert result.since == dt(
            year=2024, month=6, day=15, hour=12, minute=0, second=0
        ) - timedelta(days=1)

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

    def test_should_return_calendar_month_for_year_month_string(self):
        result = parse_time_period("2026-03")

        assert result.since == dt(year=2026, month=3, day=1)
        assert result.until == dt(year=2026, month=4, day=1)

    def test_should_cross_year_boundary_for_december(self):
        result = parse_time_period("2025-12")

        assert result.since == dt(year=2025, month=12, day=1)
        assert result.until == dt(year=2026, month=1, day=1)

    def test_should_raise_for_invalid_month_in_year_month(self):
        with pytest.raises(ValueError, match="Unsupported period"):
            parse_time_period("2026-13")


class TestMonthRange:
    def test_should_raise_for_month_zero(self):
        with pytest.raises(ValueError, match="Unsupported period"):
            month_range(2026, 0)

    def test_should_raise_for_month_thirteen(self):
        with pytest.raises(ValueError, match="Unsupported period"):
            month_range(2026, 13)


class TestGetLastMonth:
    @freeze_time("2024-06-15 12:00:00")
    def test_should_return_last_month_range_mid_month(self):
        result = get_last_month()

        assert result.since == dt(year=2024, month=5, day=1)
        assert result.until == dt(year=2024, month=6, day=1)

    @freeze_time("2024-01-15 12:00:00")
    def test_should_cross_year_boundary(self):
        result = get_last_month()

        assert result.since == dt(year=2023, month=12, day=1)
        assert result.until == dt(year=2024, month=1, day=1)

    @freeze_time("2024-03-01 00:00:00")
    def test_should_handle_first_of_month(self):
        result = get_last_month()

        assert result.since == dt(year=2024, month=2, day=1)
        assert result.until == dt(year=2024, month=3, day=1)

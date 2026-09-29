"""Unit tests for date_utils.py functions."""

import pytest
from freezegun import freeze_time

from git_dev_metrics.utils import TimePeriod, current_month, get_last_month
from git_dev_metrics.utils.date_utils import month_range

from ..conftest import dt


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


class TestMonthRange:
    def test_should_raise_for_month_zero(self):
        with pytest.raises(ValueError, match="Unsupported period"):
            month_range(2026, 0)

    def test_should_raise_for_month_thirteen(self):
        with pytest.raises(ValueError, match="Unsupported period"):
            month_range(2026, 13)


class TestCurrentMonth:
    @freeze_time("2026-09-29 08:00:00")
    def test_should_return_current_calendar_month(self):
        assert current_month() == (2026, 9)

    def test_should_use_injected_clock(self):
        assert current_month(clock=lambda: dt(year=2025, month=1, day=31)) == (2025, 1)


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

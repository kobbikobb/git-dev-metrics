"""Unit tests for default output path naming."""

from pathlib import Path

from freezegun import freeze_time

from git_dev_metrics.metrics.printer.utils import get_default_output_path


class TestGetDefaultOutputPath:
    @freeze_time("2026-05-08 09:04:07")
    def test_should_encode_simple_period_after_timestamp(self):
        result = get_default_output_path("30d")

        assert result == Path("./metrics_results/metrics_2026-05-08_09-04-07_30d.md")

    @freeze_time("2026-05-08 09:04:07")
    def test_should_swap_underscore_in_period_to_hyphen(self):
        result = get_default_output_path("last_month")

        assert result == Path("./metrics_results/metrics_2026-05-08_09-04-07_last-month.md")

    @freeze_time("2026-05-08 09:04:07")
    def test_should_pass_through_year_month_period(self):
        result = get_default_output_path("2026-03")

        assert result == Path("./metrics_results/metrics_2026-05-08_09-04-07_2026-03.md")

    @freeze_time("2026-05-08 09:04:07")
    def test_should_omit_suffix_when_period_empty(self):
        result = get_default_output_path()

        assert result == Path("./metrics_results/metrics_2026-05-08_09-04-07.md")

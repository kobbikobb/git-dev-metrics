"""Unit tests for metrics/loader.py."""

from git_dev_metrics.metrics.loader import (
    InvalidRangeError,
    load_snapshot_for_months,
    load_snapshot_for_range,
)

from ..conftest import any_pr


class TestLoadSnapshotForMonths:
    def test_should_return_none_when_no_data(self, mocker):
        mocker.patch(
            "git_dev_metrics.metrics.loader.load_all_repos_for_range",
            return_value={},
        )

        result = load_snapshot_for_months([(2026, 4)], None)

        assert result is None

    def test_should_return_snapshot_when_data_exists(self, mocker):
        repo_prs = {"org/repo": [any_pr()]}
        mocker.patch(
            "git_dev_metrics.metrics.loader.load_all_repos_for_range",
            return_value=repo_prs,
        )

        result = load_snapshot_for_months([(2026, 4)], None)

        assert result is not None
        assert result.team.pr_count == 1
        assert result.period.since.year == 2026
        assert result.period.since.month == 4

    def test_should_build_range_period_from_months(self, mocker):
        repo_prs = {"org/repo": [any_pr()]}
        mocker.patch(
            "git_dev_metrics.metrics.loader.load_all_repos_for_range",
            return_value=repo_prs,
        )

        result = load_snapshot_for_months([(2026, 1), (2026, 3)], None)

        assert result is not None
        assert result.period.since.year == 2026
        assert result.period.since.month == 1
        assert result.period.since.day == 1
        assert result.period.until.month == 4
        assert result.period.until.day == 1


class TestLoadSnapshotForRange:
    def test_should_parse_and_load_range(self, mocker):
        repo_prs = {"org/repo": [any_pr()]}
        mocker.patch(
            "git_dev_metrics.metrics.loader.load_all_repos_for_range",
            return_value=repo_prs,
        )

        result = load_snapshot_for_range("2026-04", "2026-06", None)

        assert result is not None
        assert result.team.pr_count == 1

    def test_should_raise_on_inverted_range(self, mocker):
        mocker.patch(
            "git_dev_metrics.metrics.loader.load_all_repos_for_range",
            return_value={},
        )

        exc = None
        try:
            load_snapshot_for_range("2026-06", "2026-04", None)
        except InvalidRangeError as e:
            exc = e

        assert exc is not None
        assert "--to must be >= --from" in str(exc)

    def test_should_raise_on_bad_month_format(self, mocker):
        mocker.patch(
            "git_dev_metrics.metrics.loader.load_all_repos_for_range",
            return_value={},
        )

        exc = None
        try:
            load_snapshot_for_range("bad", "2026-04", None)
        except ValueError as e:
            exc = e

        assert exc is not None
        assert "Expected YYYY-MM" in str(exc)

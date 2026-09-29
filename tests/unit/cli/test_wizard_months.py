"""Unit tests for the shared report-wizard month prompt."""

from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from git_dev_metrics.cli.wizards._wizard import _prompt_months, default_month


def _patch_checkbox(mocker, answer: list[tuple[int, int]]) -> list:
    choices: list = []

    def fake_checkbox(*_args, **_kwargs):
        choices.extend(_kwargs["choices"])
        return Mock(ask=Mock(return_value=answer))

    mocker.patch("git_dev_metrics.cli.wizards._wizard.questionary.checkbox", fake_checkbox)
    return choices


class TestDefaultMonth:
    @freeze_time("2026-09-15 09:00:00")
    def test_should_pick_current_month_when_synced(self):
        months = [(2026, 9), (2026, 8), (2026, 7)]

        assert default_month(months) == (2026, 9)

    @freeze_time("2026-09-15 09:00:00")
    def test_should_fall_back_to_newest_when_current_not_synced(self):
        months = [(2026, 8), (2026, 7), (2026, 6)]

        assert default_month(months) == (2026, 8)

    def test_should_raise_for_empty_months(self):
        with pytest.raises(ValueError, match="months must not be empty"):
            default_month([])


class TestPromptMonths:
    @freeze_time("2026-09-15 09:00:00")
    def test_should_preselect_only_current_month(self, mocker):
        choices = _patch_checkbox(mocker, [(2026, 9)])

        _prompt_months([(2026, 9), (2026, 8), (2026, 7)])

        assert [c.checked for c in choices] == [True, False, False]
        assert [c.title for c in choices] == [
            "September 2026 (current)",
            "August 2026",
            "July 2026",
        ]

    @freeze_time("2026-09-15 09:00:00")
    def test_should_preselect_newest_and_label_it_when_current_missing(self, mocker):
        choices = _patch_checkbox(mocker, [(2026, 8)])

        _prompt_months([(2026, 8), (2026, 7)])

        assert [c.checked for c in choices] == [True, False]
        assert choices[0].title == "August 2026 (latest synced)"

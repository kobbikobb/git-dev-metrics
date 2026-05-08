"""Unit tests for prompts.py functions."""

from datetime import UTC, datetime

from freezegun import freeze_time

from git_dev_metrics.cli.prompts import (
    CUSTOM_MONTH_SENTINEL,
    MAX_RESULT_FILES,
    PERIOD_OPTIONS,
    PICK_MONTH_SENTINEL,
    _last_six_months,
    _validate_year_month,
    prompt_month_selection,
    prompt_open_result,
    prompt_period_selection,
)


class TestPromptPeriodSelection:
    def test_should_return_valid_default_when_none(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        result = prompt_period_selection(default=None)

        mock_select.assert_called_once()
        assert result == "30d"

    def test_should_use_valid_default(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = "60d"

        result = prompt_period_selection(default="60d")

        call_kwargs = mock_select.call_args[1]
        assert call_kwargs["default"] == "60d"
        assert result == "60d"

    def test_should_fallback_to_30d_for_invalid_default(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        result = prompt_period_selection(default="1m")

        call_kwargs = mock_select.call_args[1]
        assert call_kwargs["default"] == "30d"
        assert result == "30d"

    def test_should_fallback_to_30d_for_unknown_value(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        result = prompt_period_selection(default="invalid")

        call_kwargs = mock_select.call_args[1]
        assert call_kwargs["default"] == "30d"
        assert result == "30d"

    def test_should_include_all_period_options_in_choices(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = "30d"

        prompt_period_selection(default="30d")

        call_kwargs = mock_select.call_args[1]
        choice_values = {c.value for c in call_kwargs["choices"]}
        expected_values = {value for _, value in PERIOD_OPTIONS}
        assert choice_values == expected_values

    def test_should_accept_last_month_as_valid_default(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = "last_month"

        result = prompt_period_selection(default="last_month")

        call_kwargs = mock_select.call_args[1]
        assert call_kwargs["default"] == "last_month"
        assert result == "last_month"


class TestPromptMonthSelection:
    @freeze_time("2026-05-08 12:00:00")
    def test_should_return_selected_year_month_value(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = "2026-03"

        result = prompt_month_selection()

        assert result == "2026-03"

    @freeze_time("2026-05-08 12:00:00")
    def test_should_offer_six_months_newest_first_plus_custom(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = "2026-05"

        prompt_month_selection()

        choices = mock_select.call_args[1]["choices"]
        values = [c.value for c in choices]
        assert values == [
            "2026-05",
            "2026-04",
            "2026-03",
            "2026-02",
            "2026-01",
            "2025-12",
            CUSTOM_MONTH_SENTINEL,
        ]

    @freeze_time("2026-05-08 12:00:00")
    def test_should_prompt_for_custom_year_month_when_chosen(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = CUSTOM_MONTH_SENTINEL
        mock_text = mocker.patch("git_dev_metrics.cli.prompts.questionary.text")
        mock_text.return_value.ask.return_value = "2025-11"

        result = prompt_month_selection()

        assert result == "2025-11"
        mock_text.assert_called_once()

    @freeze_time("2026-05-08 12:00:00")
    def test_should_return_none_when_user_aborts_main(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        assert prompt_month_selection() is None


class TestValidateYearMonth:
    def test_should_accept_valid_year_month(self):
        assert _validate_year_month("2026-03") is True

    def test_should_reject_invalid_month(self):
        assert isinstance(_validate_year_month("2026-13"), str)

    def test_should_reject_garbage(self):
        assert isinstance(_validate_year_month("foo"), str)


class TestLastSixMonths:
    def test_should_handle_year_boundary(self):
        result = _last_six_months(datetime(2026, 2, 15, tzinfo=UTC))

        values = [v for _, v in result]
        assert values == ["2026-02", "2026-01", "2025-12", "2025-11", "2025-10", "2025-09"]


class TestPromptPeriodSelectionWithMonth:
    @freeze_time("2026-05-08 12:00:00")
    def test_should_drill_into_month_picker_when_sentinel_selected(self, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.side_effect = [PICK_MONTH_SENTINEL, "2026-03"]

        result = prompt_period_selection(default="30d")

        assert result == "2026-03"
        assert mock_select.call_count == 2


class TestPromptOpenResult:
    def test_should_return_silently_when_no_files(self, tmp_path, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_select.assert_not_called()

    def test_should_offer_most_recent_files_first(self, tmp_path, mocker):
        for i, name in enumerate(["metrics_a.md", "metrics_b.md", "metrics_c.md"]):
            f = tmp_path / name
            f.write_text("x")
            import os

            os.utime(f, (i, i))
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        prompt_open_result(tmp_path / "metrics_unused.md")

        call_kwargs = mock_select.call_args[1]
        titles = [c.title for c in call_kwargs["choices"]]
        assert titles[:3] == ["metrics_c.md", "metrics_b.md", "metrics_a.md"]
        assert titles[-1] == "(skip)"

    def test_should_cap_at_max_result_files(self, tmp_path, mocker):
        for i in range(MAX_RESULT_FILES + 5):
            (tmp_path / f"metrics_{i:02d}.md").write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        prompt_open_result(tmp_path / "metrics_unused.md")

        call_kwargs = mock_select.call_args[1]
        file_choices = [c for c in call_kwargs["choices"] if c.value is not False]
        assert len(file_choices) == MAX_RESULT_FILES

    def test_should_launch_selected_file(self, tmp_path, mocker):
        target = tmp_path / "metrics_pick.md"
        target.write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = target
        mock_launch = mocker.patch("git_dev_metrics.cli.prompts.click.launch")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_launch.assert_called_once_with(str(target))

    def test_should_skip_launch_when_user_aborts(self, tmp_path, mocker):
        (tmp_path / "metrics_a.md").write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None
        mock_launch = mocker.patch("git_dev_metrics.cli.prompts.click.launch")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_launch.assert_not_called()

    def test_should_skip_launch_when_user_picks_skip_option(self, tmp_path, mocker):
        (tmp_path / "metrics_a.md").write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = False
        mock_launch = mocker.patch("git_dev_metrics.cli.prompts.click.launch")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_launch.assert_not_called()

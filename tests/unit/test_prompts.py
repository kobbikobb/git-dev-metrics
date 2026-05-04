"""Unit tests for prompts.py functions."""

from git_dev_metrics.cli.prompts import PERIOD_OPTIONS, prompt_period_selection


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

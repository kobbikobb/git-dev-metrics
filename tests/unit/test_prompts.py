"""Unit tests for prompts.py functions."""

from git_dev_metrics.cli.prompts import (
    MAX_RESULT_FILES,
    PERIOD_OPTIONS,
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


class TestPromptOpenResult:
    def test_should_return_silently_when_no_files(self, tmp_path, mocker):
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_select.assert_not_called()

    def test_should_offer_most_recent_files_first(self, tmp_path, mocker):
        for i, name in enumerate(["metrics_a.html", "metrics_b.html", "metrics_c.html"]):
            f = tmp_path / name
            f.write_text("x")
            import os

            os.utime(f, (i, i))
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        prompt_open_result(tmp_path / "metrics_unused.md")

        call_kwargs = mock_select.call_args[1]
        titles = [c.title for c in call_kwargs["choices"]]
        assert titles[:3] == ["metrics_c.html", "metrics_b.html", "metrics_a.html"]
        assert titles[-1] == "(skip)"

    def test_should_cap_at_max_result_files(self, tmp_path, mocker):
        for i in range(MAX_RESULT_FILES + 5):
            (tmp_path / f"metrics_{i:02d}.html").write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        prompt_open_result(tmp_path / "metrics_unused.md")

        call_kwargs = mock_select.call_args[1]
        file_choices = [c for c in call_kwargs["choices"] if c.value is not False]
        assert len(file_choices) == MAX_RESULT_FILES

    def test_should_launch_selected_file(self, tmp_path, mocker):
        target = tmp_path / "metrics_pick.html"
        target.write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = target
        mock_launch = mocker.patch("git_dev_metrics.cli.prompts.click.launch")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_launch.assert_called_once_with(str(target))

    def test_should_skip_launch_when_user_aborts(self, tmp_path, mocker):
        (tmp_path / "metrics_a.html").write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None
        mock_launch = mocker.patch("git_dev_metrics.cli.prompts.click.launch")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_launch.assert_not_called()

    def test_should_skip_launch_when_user_picks_skip_option(self, tmp_path, mocker):
        (tmp_path / "metrics_a.html").write_text("x")
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = False
        mock_launch = mocker.patch("git_dev_metrics.cli.prompts.click.launch")

        prompt_open_result(tmp_path / "metrics_unused.md")

        mock_launch.assert_not_called()

    def test_should_include_both_html_and_md_files(self, tmp_path, mocker):
        import os

        for i, name in enumerate(["metrics_a.html", "metrics_a.md"]):
            f = tmp_path / name
            f.write_text("x")
            os.utime(f, (i, i))
        mock_select = mocker.patch("git_dev_metrics.cli.prompts.questionary.select")
        mock_select.return_value.ask.return_value = None

        prompt_open_result(tmp_path / "metrics_unused.md")

        call_kwargs = mock_select.call_args[1]
        titles = [c.title for c in call_kwargs["choices"]]
        assert "metrics_a.html" in titles
        assert "metrics_a.md" in titles

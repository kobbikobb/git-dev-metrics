from typer.testing import CliRunner

from git_dev_metrics.cli import app

runner = CliRunner()


class TestCLI:
    def test_should_show_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_should_reject_invalid_period(self):
        result = runner.invoke(app, ["--org", "x", "--repo", "y", "--period", "invalid"])
        assert result.exit_code != 0

    def test_should_run_without_period(self, mocker):
        mocker.patch("git_dev_metrics.cli.get_github_token", return_value="fake-token")
        mock_get_prs = mocker.patch(
            "git_dev_metrics.cli.get_pull_request_metrics", return_value={"commits": 10, "prs": 5}
        )
        mock_print = mocker.patch("git_dev_metrics.cli.print_metrics")

        result = runner.invoke(app, ["--org", "facebook", "--repo", "react"])

        mock_get_prs.assert_called_once_with("fake-token", "facebook", "react", "30d")
        mock_print.assert_called_once()
        assert result.exit_code == 0

    def test_should_accept_valid_period(self, mocker):
        mocker.patch("git_dev_metrics.cli.get_github_token", return_value="fake-token")
        mock_get_prs = mocker.patch(
            "git_dev_metrics.cli.get_pull_request_metrics", return_value={"commits": 10, "prs": 5}
        )
        mock_print = mocker.patch("git_dev_metrics.cli.print_metrics")

        result = runner.invoke(app, ["--org", "facebook", "--repo", "react", "--period", "7d"])

        mock_get_prs.assert_called_once_with("fake-token", "facebook", "react", "7d")
        mock_print.assert_called_once()
        assert result.exit_code == 0

    def test_should_handle_client_error(self, mocker):
        mocker.patch("git_dev_metrics.cli.get_github_token", return_value="fake-token")
        mock_get_prs = mocker.patch("git_dev_metrics.cli")
        mock_get_prs.return_value.get_pull_request_metrics.side_effect = Exception("API Error")

        result = runner.invoke(app, ["--org", "facebook", "--repo", "react"])

        assert result.exit_code == 1

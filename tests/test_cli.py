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
        mock_get_token = mocker.patch('git_dev_metrics.cli.get_github_token', return_value="fake-token")
        mock_client = mocker.patch('git_dev_metrics.cli.GitHubClient')
        mock_client.return_value.get_development_metrics.return_value = {"commits": 10, "prs": 5}
        mock_print = mocker.patch('git_dev_metrics.cli.print_metrics')

        result = runner.invoke(app, ["--org", "facebook", "--repo", "react"])

        assert result.exit_code == 0
        mock_get_token.assert_called_once()
        mock_client.assert_called_once_with("fake-token", "facebook", "react")
        mock_client.return_value.get_development_metrics.assert_called_once_with("30d")
        mock_print.assert_called_once()

    def test_should_accept_valid_period(self, mocker):
        mock_get_token = mocker.patch('git_dev_metrics.cli.get_github_token', return_value="fake-token")
        mock_client = mocker.patch('git_dev_metrics.cli.GitHubClient')
        mock_client.return_value.get_development_metrics.return_value = {"commits": 10, "prs": 5}
        mock_print = mocker.patch('git_dev_metrics.cli.print_metrics')

        result = runner.invoke(app, ["--org", "facebook", "--repo", "react", "--period", "7d"])

        assert result.exit_code == 0
        mock_client.return_value.get_development_metrics.assert_called_once_with("7d")

    def test_should_handle_client_error(self, mocker):
        mocker.patch('git_dev_metrics.cli.get_github_token', return_value="fake-token")
        mock_client = mocker.patch('git_dev_metrics.cli.GitHubClient')
        mock_client.return_value.get_development_metrics.side_effect = Exception("API Error")
        mocker.patch('git_dev_metrics.cli.print_metrics')

        result = runner.invoke(app, ["--org", "facebook", "--repo", "react"])

        assert result.exit_code == 1

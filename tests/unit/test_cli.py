from typer.testing import CliRunner

from git_dev_metrics.main import app

runner = CliRunner()


class TestCLI:
    def test_should_show_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_should_reject_invalid_period(self):
        result = runner.invoke(app, ["--period", "invalid"])
        assert result.exit_code != 0

    def test_should_run_without_period(self, mocker):
        mocker.patch("git_dev_metrics.cli.runner.get_github_token", return_value="fake-token")
        mock_get_prs = mocker.patch(
            "git_dev_metrics.cli.runner.get_combined_metrics",
            return_value={"repo_metrics": {}, "dev_metrics": {}},
        )
        mocker.patch("git_dev_metrics.cli.output._print_combined_metrics")
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_org_selection",
            return_value="test-org",
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_repo_selection",
            return_value=["test-org/repo1", "test-org/repo2"],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_organizations",
            return_value=[{"login": "test-org", "name": "Test Org"}],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_org_repositories",
            return_value=[
                {"full_name": "test-org/repo1", "private": False, "last_pushed": None},
                {"full_name": "test-org/repo2", "private": True, "last_pushed": None},
            ],
        )

        result = runner.invoke(app, [])

        mock_get_prs.assert_called_once_with(
            "fake-token", ["test-org/repo1", "test-org/repo2"], "30d"
        )
        assert result.exit_code == 0

    def test_should_accept_valid_period(self, mocker):
        mocker.patch("git_dev_metrics.cli.runner.get_github_token", return_value="fake-token")
        mock_get_prs = mocker.patch(
            "git_dev_metrics.cli.runner.get_combined_metrics",
            return_value={"repo_metrics": {}, "dev_metrics": {}},
        )
        mocker.patch("git_dev_metrics.cli.output._print_combined_metrics")
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_org_selection",
            return_value="test-org",
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_repo_selection",
            return_value=["test-org/repo1"],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_organizations",
            return_value=[{"login": "test-org", "name": "Test Org"}],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_org_repositories",
            return_value=[{"full_name": "test-org/repo1", "private": False, "last_pushed": None}],
        )

        result = runner.invoke(app, ["--period", "7d"])

        mock_get_prs.assert_called_once_with("fake-token", ["test-org/repo1"], "7d")
        assert result.exit_code == 0

    def test_should_handle_client_error(self, mocker):
        mocker.patch("git_dev_metrics.cli.runner.get_github_token", return_value="fake-token")
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_org_selection",
            return_value="test-org",
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_repo_selection",
            return_value=["test-org/repo1"],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_organizations",
            return_value=[{"login": "test-org", "name": "Test Org"}],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_org_repositories",
            return_value=[{"full_name": "test-org/repo1", "private": False, "last_pushed": None}],
        )
        mock_get_prs = mocker.patch("git_dev_metrics.cli.runner.get_combined_metrics")
        mock_get_prs.side_effect = Exception("API Error")

        result = runner.invoke(app, [])

        assert result.exit_code == 1

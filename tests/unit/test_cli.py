from typer.testing import CliRunner

from git_dev_metrics.main import app

runner = CliRunner()


class TestCLI:
    def test_should_show_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_should_run(self, mocker):
        mocker.patch("git_dev_metrics.cli.runner.get_github_token", return_value="fake-token")
        mocker.patch("git_dev_metrics.cli.runner.load_last_period", return_value=None)
        mocker.patch("git_dev_metrics.cli.runner.save_last_period")
        mocker.patch("git_dev_metrics.cli.runner.load_last_org", return_value=None)
        mocker.patch("git_dev_metrics.cli.runner.save_last_org")
        mock_get_prs = mocker.patch(
            "git_dev_metrics.cli.runner.get_combined_metrics",
            return_value={"repo_metrics": {}, "dev_metrics": {}},
        )
        mocker.patch("git_dev_metrics.cli.output._print_combined_metrics")
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_period_selection",
            return_value="30d",
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_org_name",
            return_value="test-org",
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_repo_selection",
            return_value=["test-org/repo1", "test-org/repo2"],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_org_repositories",
            return_value=[
                {"full_name": "test-org/repo1", "private": False, "last_pushed": None},
                {"full_name": "test-org/repo2", "private": True, "last_pushed": None},
            ],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner._filter_repos_by_period",
            side_effect=lambda repos, since: repos,
        )

        result = runner.invoke(app, [])

        mock_get_prs.assert_called_once_with(
            "fake-token", ["test-org/repo1", "test-org/repo2"], "30d"
        )
        assert result.exit_code == 0

    def test_should_handle_client_error(self, mocker):
        mocker.patch("git_dev_metrics.cli.runner.get_github_token", return_value="fake-token")
        mocker.patch("git_dev_metrics.cli.runner.load_last_period", return_value=None)
        mocker.patch("git_dev_metrics.cli.runner.save_last_period")
        mocker.patch("git_dev_metrics.cli.runner.load_last_org", return_value=None)
        mocker.patch("git_dev_metrics.cli.runner.save_last_org")
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_period_selection",
            return_value="30d",
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_org_name",
            return_value="test-org",
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.prompt_repo_selection",
            return_value=["test-org/repo1"],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner.fetch_org_repositories",
            return_value=[{"full_name": "test-org/repo1", "private": False, "last_pushed": None}],
        )
        mocker.patch(
            "git_dev_metrics.cli.runner._filter_repos_by_period",
            side_effect=lambda repos, since: repos,
        )
        mock_get_prs = mocker.patch("git_dev_metrics.cli.runner.get_combined_metrics")
        mock_get_prs.side_effect = Exception("API Error")

        result = runner.invoke(app, [])

        assert result.exit_code == 1

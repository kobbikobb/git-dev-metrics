from freezegun import freeze_time
from typer.testing import CliRunner

from git_dev_metrics.cache import count_prs, seal_month
from git_dev_metrics.cli.app import app

from ..conftest import any_pr, approved_review, dt

runner = CliRunner()


def _ten_prs_for_april() -> list:
    days = [1, 3, 5, 8, 12, 15, 18, 22, 25, 29]
    logins = ["a", "b", "c", "a", "d", "b", "e", "a", "f", "c"]
    return [
        any_pr(
            id=100 + i,
            number=200 + i,
            user={"login": logins[i]},
            created_at=dt(year=2026, month=4, day=day, hour=8, minute=0),
            merged_at=dt(year=2026, month=4, day=day, hour=18, minute=0),
            reviews=[approved_review(login="reviewer-1")] if i % 3 == 0 else [],
        )
        for i, day in enumerate(days)
    ]


class TestPull:
    @freeze_time("2026-05-12")
    def test_should_write_prs_and_seal_month(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        prs = _ten_prs_for_april()
        mocker.patch("git_dev_metrics.cli.commands.pull.get_github_token", return_value="fake-token")
        mocker.patch("git_dev_metrics.cli.runners.pull_runner.fetch_repo_metrics", return_value=prs)

        result = runner.invoke(
            app,
            [
                "pull",
                "--month",
                "2026-04",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
            ],
        )

        assert result.exit_code == 0
        assert count_prs("myorg", "myrepo", 2026, 4, db_path=db_path) == 10
        from git_dev_metrics.cache import is_sealed, open_connection

        assert is_sealed("myorg", "myrepo", 2026, 4, db_path=db_path)
        conn = open_connection(db_path)
        review_count = conn.execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
        conn.close()
        assert review_count > 0

    @freeze_time("2026-05-12")
    def test_should_refuse_incomplete_current_month(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        mocker.patch("git_dev_metrics.cli.commands.pull.get_github_token", return_value="fake-token")
        fetch = mocker.patch("git_dev_metrics.cli.runners.pull_runner.fetch_repo_metrics", return_value=[])

        result = runner.invoke(
            app,
            [
                "pull",
                "--month",
                "2026-05",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
            ],
        )

        assert result.exit_code == 1
        assert "incomplete" in result.stderr
        fetch.assert_not_called()
        assert count_prs("myorg", "myrepo", 2026, 5, db_path=db_path) == 0

    def test_should_invoke_wizard_when_no_flags(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        wizard = mocker.patch("git_dev_metrics.cli.commands.pull.pull_wizard")

        result = runner.invoke(app, ["pull", "--db", str(db_path)])

        assert result.exit_code == 0, result.output
        wizard.assert_called_once_with(db_path=db_path)

    @freeze_time("2026-05-12")
    def test_should_refuse_already_sealed_month(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "myrepo", 2026, 4, db_path=db_path)
        mocker.patch("git_dev_metrics.cli.commands.pull.get_github_token", return_value="fake-token")
        fetch = mocker.patch("git_dev_metrics.cli.runners.pull_runner.fetch_repo_metrics", return_value=[])

        result = runner.invoke(
            app,
            [
                "pull",
                "--month",
                "2026-04",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
            ],
        )

        assert result.exit_code == 1
        assert "already sealed" in result.stderr
        fetch.assert_not_called()
        assert count_prs("myorg", "myrepo", 2026, 4, db_path=db_path) == 0

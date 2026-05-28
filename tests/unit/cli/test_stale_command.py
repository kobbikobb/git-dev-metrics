from datetime import datetime

from freezegun import freeze_time
from typer.testing import CliRunner

from git_dev_metrics.cache import seal_month
from git_dev_metrics.cli import app

from ..conftest import dt

runner = CliRunner()


def _open_pr(number: int, login: str, created_at: datetime, is_draft: bool = False) -> dict:
    return {
        "number": number,
        "title": f"PR #{number}",
        "created_at": created_at,
        "merged_at": None,
        "user": {"login": login},
        "is_draft": is_draft,
        "is_approved": False,
    }


class TestStale:
    @freeze_time("2026-05-12")
    def test_should_render_html_for_stale_prs_across_synced_repos(
        self, tmp_path, mocker, _stub_webbrowser
    ):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
        seal_month("myorg", "repoB", 2026, 4, db_path=db_path)

        def fake_open_prs(_token, _org, repo, **_kwargs):
            if repo == "repoA":
                return [
                    _open_pr(1, "alice", dt(year=2026, month=4, day=1, hour=8, minute=0))
                ]  # ~41d
            return [_open_pr(2, "bob", dt(year=2026, month=5, day=1, hour=8, minute=0))]  # ~11d

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch("git_dev_metrics.cli.commands.stale.fetch_open_prs", side_effect=fake_open_prs)
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "Stale PRs" in html
        assert "myorg/repoA" in html
        assert "myorg/repoB" in html
        assert "alice" in html
        assert "bob" in html
        _stub_webbrowser.assert_called_once_with(out.resolve().as_uri())

    @freeze_time("2026-05-12")
    def test_should_sort_oldest_first(self, tmp_path, mocker, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[
                _open_pr(10, "young", dt(year=2026, month=5, day=1, hour=8, minute=0)),  # ~11d
                _open_pr(11, "old", dt(year=2026, month=4, day=1, hour=8, minute=0)),  # ~41d
            ],
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        old_idx = html.find("#11")
        young_idx = html.find("#10")
        assert 0 < old_idx < young_idx

    @freeze_time("2026-05-12")
    def test_should_render_empty_state_when_no_stale_prs(self, tmp_path, mocker, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[
                _open_pr(1, "alice", dt(year=2026, month=5, day=10, hour=8, minute=0))
            ],  # ~2d, fresh
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        assert "No stale PRs" in out.read_text()

    def test_should_exit_when_no_repos_in_cache(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path)])

        # Assert
        assert result.exit_code == 1
        assert "No repos in cache" in result.stderr

    @freeze_time("2026-05-12")
    def test_should_write_default_path_when_no_output(
        self, tmp_path, monkeypatch, mocker, _stub_webbrowser
    ):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
        monkeypatch.chdir(tmp_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[_open_pr(1, "alice", dt(year=2026, month=4, day=1, hour=8, minute=0))],
        )

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path)])

        # Assert
        assert result.exit_code == 0, result.output
        expected = tmp_path / "metrics_results" / "stale_2026-05-12.html"
        assert expected.exists()

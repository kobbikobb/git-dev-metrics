from datetime import datetime

import pytest
from freezegun import freeze_time
from typer.testing import CliRunner

from git_dev_metrics.cache import seal_month
from git_dev_metrics.cli import app
from git_dev_metrics.github import GitHubAuthError, GitHubNotFoundError

from ..conftest import dt

runner = CliRunner()


def _open_pr(
    number: int,
    login: str,
    created_at: datetime,
    is_draft: bool = False,
    labels: list[str] | None = None,
    build_state: str | None = None,
    head_sha: str | None = None,
) -> dict:
    return {
        "number": number,
        "title": f"PR #{number}",
        "created_at": created_at,
        "merged_at": None,
        "user": {"login": login},
        "is_draft": is_draft,
        "is_approved": False,
        "labels": labels or [],
        "head_sha": head_sha,
        "build_state": build_state,
    }


class TestStale:
    @pytest.fixture(autouse=True)
    def _no_security_alerts(self, mocker):
        mocker.patch("git_dev_metrics.cli.commands.stale.fetch_open_pr_security", return_value={})

    @pytest.fixture(autouse=True)
    def _not_archived(self, mocker):
        mocker.patch("git_dev_metrics.cli.commands.stale.is_repo_archived", return_value=False)

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
    def test_should_sort_by_age_oldest_first(self, tmp_path, mocker, _stub_webbrowser):
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
                _open_pr(12, "old", dt(year=2026, month=5, day=1, hour=8, minute=0)),  # ~11d
            ],
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        young_idx = html.find("#10")
        old_older_idx = html.find("#11")
        old_newer_idx = html.find("#12")
        # Oldest first; #10/#12 tie on age so insertion order is preserved
        assert 0 < old_older_idx < young_idx < old_newer_idx

    @freeze_time("2026-05-12")
    def test_should_render_labels(self, tmp_path, mocker, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[
                _open_pr(
                    1,
                    "alice",
                    dt(year=2026, month=4, day=1, hour=8, minute=0),
                    labels=["bug", "priority:high"],
                )
            ],
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "bug" in html
        assert "priority:high" in html

    @freeze_time("2026-05-12")
    def test_should_render_build_and_security_badges(self, tmp_path, mocker, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[
                _open_pr(
                    1,
                    "alice",
                    dt(year=2026, month=4, day=1, hour=8, minute=0),
                    build_state="FAILURE",
                )
            ],
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_pr_security",
            return_value={1: {"severity": "high", "advisory_id": "GHSA-1234"}},
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "failing" in html
        assert "high: GHSA-1234" in html

    @freeze_time("2026-05-12")
    def test_should_degrade_when_security_alerts_unreadable(
        self, tmp_path, mocker, _stub_webbrowser
    ):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[_open_pr(1, "alice", dt(year=2026, month=4, day=1, hour=8, minute=0))],
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_pr_security",
            side_effect=GitHubNotFoundError("no access"),
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "PR #1" in html
        assert "Security alerts unavailable" in result.stderr

    @freeze_time("2026-05-12")
    def test_should_warn_once_when_build_status_unavailable(
        self, tmp_path, mocker, _stub_webbrowser
    ):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[
                _open_pr(
                    1,
                    "alice",
                    dt(year=2026, month=4, day=1, hour=8, minute=0),
                    head_sha="abc123",
                )
            ],
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_pr_build_state",
            side_effect=GitHubAuthError("needs Actions: Read permission"),
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "PR #1" in html
        assert "no checks" in html
        assert "Build status unavailable" in result.stderr
        assert result.stderr.count("Build status unavailable") == 1

    @freeze_time("2026-05-12")
    def test_should_render_build_badge_from_actions(self, tmp_path, mocker, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[
                _open_pr(
                    1,
                    "alice",
                    dt(year=2026, month=4, day=1, hour=8, minute=0),
                    head_sha="abc123",
                )
            ],
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_pr_build_state",
            return_value={1: "SUCCESS"},
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "passing" in html
        assert "no checks" not in html

    @freeze_time("2026-05-12")
    def test_should_skip_repo_on_generic_github_error(self, tmp_path, mocker, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
        seal_month("myorg", "repoB", 2026, 4, db_path=db_path)

        def fake_open_prs(_token, _org, repo, **_kwargs):
            if repo == "repoA":
                raise GitHubNotFoundError("no access")
            return [_open_pr(2, "bob", dt(year=2026, month=5, day=1, hour=8, minute=0))]

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
        assert "myorg/repoB" in html
        assert "myorg/repoA" not in html
        assert "Skipping myorg/repoA" in result.stderr

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

    @freeze_time("2026-05-12")
    def test_should_skip_archived_repo(self, tmp_path, mocker, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
        seal_month("myorg", "repoB", 2026, 4, db_path=db_path)

        def fake_archived(_token, _org, repo):
            return repo == "repoA"

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token", return_value="fake-token"
        )
        mocker.patch("git_dev_metrics.cli.commands.stale.is_repo_archived", side_effect=fake_archived)
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            return_value=[
                _open_pr(2, "bob", dt(year=2026, month=5, day=1, hour=8, minute=0)),
            ],
        )
        out = tmp_path / "stale.html"

        # Act
        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "myorg/repoB" in html
        assert "myorg/repoA" not in html
        assert "Skipping myorg/repoA — archived" in result.stderr

    @freeze_time("2026-05-12")
    def test_should_skip_missing_repos(self, tmp_path, mocker, _stub_webbrowser):
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
        seal_month("myorg", "ghost-repo", 2026, 4, db_path=db_path)

        def fake_open_prs(_token, _org, repo, **_kwargs):
            if repo == "ghost-repo":
                raise GitHubNotFoundError("not found")
            return [_open_pr(1, "alice", dt(year=2026, month=4, day=1, hour=8, minute=0))]

        mocker.patch(
            "git_dev_metrics.cli.commands.stale.get_github_token",
            return_value="fake-token",
        )
        mocker.patch(
            "git_dev_metrics.cli.commands.stale.fetch_open_prs",
            side_effect=fake_open_prs,
        )
        out = tmp_path / "stale.html"

        result = runner.invoke(app, ["stale", "--db", str(db_path), "--output", str(out)])

        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "myorg/repoA" in html
        assert "myorg/ghost-repo" not in html
        assert "Skipping" in result.stderr

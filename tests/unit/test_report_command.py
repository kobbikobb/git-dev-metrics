from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli.app import app

from .conftest import any_pr, approved_review

runner = CliRunner()


def _seed_two_repos_apr(db_path) -> None:
    """3 merged PRs across 2 repos and 2 devs in April 2026."""
    repo_a = [
        any_pr(
            number=11,
            user={"login": "alice"},
            additions=120,
            deletions=30,
            changed_files=4,
            created_at="2026-04-02T09:00:00Z",
            merged_at="2026-04-03T10:00:00Z",
            closed_at="2026-04-03T10:00:00Z",
            reviews=[approved_review(login="bob", submitted_at="2026-04-02T15:00:00Z")],
        ),
        any_pr(
            number=12,
            user={"login": "bob"},
            additions=60,
            deletions=20,
            changed_files=3,
            created_at="2026-04-10T09:00:00Z",
            merged_at="2026-04-11T11:00:00Z",
            closed_at="2026-04-11T11:00:00Z",
            reviews=[approved_review(login="alice", submitted_at="2026-04-10T18:00:00Z")],
        ),
    ]
    repo_b = [
        any_pr(
            number=21,
            user={"login": "alice"},
            additions=40,
            deletions=10,
            changed_files=2,
            created_at="2026-04-15T09:00:00Z",
            merged_at="2026-04-16T13:00:00Z",
            closed_at="2026-04-16T13:00:00Z",
            reviews=[approved_review(login="bob", submitted_at="2026-04-15T17:00:00Z")],
        ),
    ]
    insert_prs(repo_a, "myorg", "repoA", 2026, 4, db_path=db_path)
    insert_prs(repo_b, "myorg", "repoB", 2026, 4, db_path=db_path)
    seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
    seal_month("myorg", "repoB", 2026, 4, db_path=db_path)


class TestReportFlagMode:
    def test_should_render_markdown_aggregated_across_repos(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        out = tmp_path / "r.md"

        # Act
        result = runner.invoke(
            app,
            [
                "report",
                "--from",
                "2026-04",
                "--to",
                "2026-04",
                "--output",
                str(out),
                "--db",
                str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        md = out.read_text()
        assert "# Summary (2026-04-01 to 2026-05-01)" in md
        assert "Total PRs" in md
        assert "Median Cycle Time" in md
        assert "myorg/repoA" in md
        assert "myorg/repoB" in md

    def test_should_render_html_when_output_suffix_html(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        out = tmp_path / "r.html"

        # Act
        result = runner.invoke(
            app,
            [
                "report",
                "--from",
                "2026-04",
                "--to",
                "2026-04",
                "--output",
                str(out),
                "--db",
                str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        html = out.read_text().lower()
        assert "<html" in html
        assert "alice" in html
        assert "bob" in html

    def test_should_write_default_path_with_range_slug(self, tmp_path, monkeypatch):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(
            app,
            [
                "report",
                "--from",
                "2026-04",
                "--to",
                "2026-04",
                "--db",
                str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        results_dir = tmp_path / "metrics_results"
        assert list(results_dir.glob("metrics_*_2026-04-to-2026-04.md"))
        assert list(results_dir.glob("metrics_*_2026-04-to-2026-04.html"))

    def test_should_exit_when_no_synced_data_in_range(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"

        # Act
        result = runner.invoke(
            app,
            [
                "report",
                "--from",
                "2026-04",
                "--to",
                "2026-04",
                "--db",
                str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 1
        assert "No synced data" in result.stderr

    def test_should_reject_inverted_range(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)

        # Act
        result = runner.invoke(
            app,
            [
                "report",
                "--from",
                "2026-04",
                "--to",
                "2026-02",
                "--db",
                str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 1
        assert "--to must be >= --from" in result.stderr


class TestReportWizardDispatch:
    def test_should_invoke_wizard_when_no_flags(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        wizard = mocker.patch("git_dev_metrics.cli.report.report_wizard")

        result = runner.invoke(app, ["report", "--db", str(db_path)])

        assert result.exit_code == 0, result.output
        wizard.assert_called_once_with(db_path=db_path)


class TestReportOpensBrowser:
    def test_should_open_html_in_browser_for_default_output(
        self, tmp_path, monkeypatch, _stub_webbrowser
    ):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(
            app,
            ["report", "--from", "2026-04", "--to", "2026-04", "--db", str(db_path)],
        )

        # Assert
        assert result.exit_code == 0, result.output
        _stub_webbrowser.assert_called_once()
        uri = _stub_webbrowser.call_args.args[0]
        assert uri.startswith("file://")
        assert uri.endswith("_2026-04-to-2026-04.html")

    def test_should_open_html_when_output_suffix_html(self, tmp_path, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        out = tmp_path / "r.html"

        # Act
        result = runner.invoke(
            app,
            [
                "report", "--from", "2026-04", "--to", "2026-04",
                "--output", str(out), "--db", str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        _stub_webbrowser.assert_called_once()
        assert _stub_webbrowser.call_args.args[0] == out.resolve().as_uri()

    def test_should_not_open_when_output_is_markdown(self, tmp_path, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        out = tmp_path / "r.md"

        # Act
        result = runner.invoke(
            app,
            [
                "report", "--from", "2026-04", "--to", "2026-04",
                "--output", str(out), "--db", str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        _stub_webbrowser.assert_not_called()

    def test_should_not_open_when_no_open_flag(self, tmp_path, monkeypatch, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(
            app,
            [
                "report", "--from", "2026-04", "--to", "2026-04",
                "--db", str(db_path), "--no-open",
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        _stub_webbrowser.assert_not_called()

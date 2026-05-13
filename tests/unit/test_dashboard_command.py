from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli.app import app

from .conftest import any_pr, approved_review, dt

runner = CliRunner()


def _seed_two_repos_apr(db_path) -> None:
    repo_a = [
        any_pr(
            number=11,
            user={"login": "alice"},
            additions=120,
            deletions=30,
            changed_files=4,
            created_at=dt(year=2026, month=4, day=2, hour=9, minute=0),
            merged_at=dt(year=2026, month=4, day=3, hour=10, minute=0),
            closed_at=dt(year=2026, month=4, day=3, hour=10, minute=0),
            reviews=[
                approved_review(
                    login="bob", submitted_at=dt(year=2026, month=4, day=2, hour=15, minute=0)
                )
            ],
        ),
        any_pr(
            number=12,
            user={"login": "bob"},
            additions=60,
            deletions=20,
            changed_files=3,
            created_at=dt(year=2026, month=4, day=10, hour=9, minute=0),
            merged_at=dt(year=2026, month=4, day=11, hour=11, minute=0),
            closed_at=dt(year=2026, month=4, day=11, hour=11, minute=0),
            reviews=[
                approved_review(
                    login="alice", submitted_at=dt(year=2026, month=4, day=10, hour=18, minute=0)
                )
            ],
        ),
    ]
    repo_b = [
        any_pr(
            number=21,
            user={"login": "alice"},
            additions=40,
            deletions=10,
            changed_files=2,
            created_at=dt(year=2026, month=4, day=15, hour=9, minute=0),
            merged_at=dt(year=2026, month=4, day=16, hour=13, minute=0),
            closed_at=dt(year=2026, month=4, day=16, hour=13, minute=0),
            reviews=[
                approved_review(
                    login="bob", submitted_at=dt(year=2026, month=4, day=15, hour=17, minute=0)
                )
            ],
        ),
    ]
    insert_prs(repo_a, "myorg", "repoA", 2026, 4, db_path=db_path)
    insert_prs(repo_b, "myorg", "repoB", 2026, 4, db_path=db_path)
    seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
    seal_month("myorg", "repoB", 2026, 4, db_path=db_path)


class TestDashboardFlagMode:
    def test_should_render_html_to_explicit_output(self, tmp_path, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        out = tmp_path / "r.html"

        # Act
        result = runner.invoke(
            app,
            [
                "dashboard",
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
        _stub_webbrowser.assert_called_once_with(out.resolve().as_uri())

    def test_should_write_default_path_with_range_slug(
        self, tmp_path, monkeypatch, _stub_webbrowser
    ):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        monkeypatch.chdir(tmp_path)

        # Act
        result = runner.invoke(
            app,
            ["dashboard", "--from", "2026-04", "--to", "2026-04", "--db", str(db_path)],
        )

        # Assert
        assert result.exit_code == 0, result.output
        results_dir = tmp_path / "metrics_results"
        matches = list(results_dir.glob("dashboard_*_2026-04-to-2026-04.html"))
        assert matches
        _stub_webbrowser.assert_called_once_with(matches[0].resolve().as_uri())

    def test_should_force_html_suffix_when_user_passes_non_html(self, tmp_path, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)
        out = tmp_path / "r.md"

        # Act
        result = runner.invoke(
            app,
            [
                "dashboard",
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
        written = out.with_suffix(".html")
        assert written.exists()
        _stub_webbrowser.assert_called_once_with(written.resolve().as_uri())

    def test_should_exit_when_no_synced_data_in_range(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"

        # Act
        result = runner.invoke(
            app,
            ["dashboard", "--from", "2026-04", "--to", "2026-04", "--db", str(db_path)],
        )

        # Assert
        assert result.exit_code == 1
        assert "No synced data" in result.stderr


class TestDashboardWizardDispatch:
    def test_should_invoke_wizard_when_no_flags(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        wizard = mocker.patch("git_dev_metrics.cli.dashboard.dashboard_wizard")

        result = runner.invoke(app, ["dashboard", "--db", str(db_path)])

        assert result.exit_code == 0, result.output
        wizard.assert_called_once_with(db_path=db_path)

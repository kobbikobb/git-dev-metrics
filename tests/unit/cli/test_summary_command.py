from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli import app

from ..conftest import any_pr, approved_review, dt

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


class TestSummaryFlagMode:
    def test_should_print_console_summary_for_range(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)

        # Act
        result = runner.invoke(
            app,
            ["summary", "--from", "2026-04", "--to", "2026-04", "--db", str(db_path)],
        )

        # Assert
        assert result.exit_code == 0, result.output
        out = result.output
        assert "Developer Metrics (2026-04-01 to 2026-05-01)" in out
        assert "bob" in out

    def test_should_exit_when_no_synced_data_in_range(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"

        # Act
        result = runner.invoke(
            app,
            ["summary", "--from", "2026-04", "--to", "2026-04", "--db", str(db_path)],
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
            ["summary", "--from", "2026-04", "--to", "2026-02", "--db", str(db_path)],
        )

        # Assert
        assert result.exit_code == 1
        assert "--to must be >= --from" in result.stderr

    def test_should_not_open_browser(self, tmp_path, _stub_webbrowser):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_two_repos_apr(db_path)

        # Act
        result = runner.invoke(
            app,
            ["summary", "--from", "2026-04", "--to", "2026-04", "--db", str(db_path)],
        )

        # Assert
        assert result.exit_code == 0, result.output
        _stub_webbrowser.assert_not_called()


class TestSummaryWizardDispatch:
    def test_should_invoke_wizard_when_no_flags(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        wizard = mocker.patch("git_dev_metrics.cli.commands.summary.summary_wizard")

        result = runner.invoke(app, ["summary", "--db", str(db_path)])

        assert result.exit_code == 0, result.output
        wizard.assert_called_once_with(db_path=db_path)

from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli.app import app

from ..conftest import any_pr

runner = CliRunner()


class TestClear:
    def test_should_delete_existing_cache_when_confirmed(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        insert_prs([any_pr(number=1)], "myorg", "myrepo", 2026, 4, db_path=db_path)
        seal_month("myorg", "myrepo", 2026, 4, db_path=db_path)
        assert db_path.exists()

        # Act
        result = runner.invoke(app, ["clear", "--db", str(db_path)], input="y\n")

        # Assert
        assert result.exit_code == 0, result.output
        assert not db_path.exists()
        assert "Deleted" in result.output

    def test_should_cancel_when_user_declines_confirmation(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        insert_prs([any_pr(number=1)], "myorg", "myrepo", 2026, 4, db_path=db_path)

        # Act
        result = runner.invoke(app, ["clear", "--db", str(db_path)], input="n\n")

        # Assert
        assert result.exit_code == 1
        assert db_path.exists()
        assert "Cancelled" in result.output

    def test_should_skip_confirmation_with_yes_flag(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        insert_prs([any_pr(number=1)], "myorg", "myrepo", 2026, 4, db_path=db_path)

        # Act
        result = runner.invoke(app, ["clear", "--db", str(db_path), "--yes"])

        # Assert
        assert result.exit_code == 0, result.output
        assert not db_path.exists()

    def test_should_no_op_when_cache_already_empty(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        assert not db_path.exists()

        # Act
        result = runner.invoke(app, ["clear", "--db", str(db_path)])

        # Assert
        assert result.exit_code == 0, result.output
        assert "already empty" in result.output
        assert not db_path.exists()

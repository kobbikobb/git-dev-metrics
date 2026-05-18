from typer.testing import CliRunner

from git_dev_metrics.cache import Cache
from git_dev_metrics.cli.app import app

from ..conftest import any_pr

runner = CliRunner()


class TestClear:
    def test_should_delete_existing_cache_when_confirmed(self, tmp_path):
        db_path = tmp_path / "cache.db"
        cache = Cache(db_path)
        cache.store_prs([any_pr(number=1)], "myorg", "myrepo", 2026, 4)
        cache.seal_month("myorg", "myrepo", 2026, 4)
        assert db_path.exists()

        result = runner.invoke(app, ["clear", "--db", str(db_path)], input="y\n")

        assert result.exit_code == 0, result.output
        assert not db_path.exists()
        assert "Deleted" in result.output

    def test_should_cancel_when_user_declines_confirmation(self, tmp_path):
        db_path = tmp_path / "cache.db"
        Cache(db_path).store_prs([any_pr(number=1)], "myorg", "myrepo", 2026, 4)

        result = runner.invoke(app, ["clear", "--db", str(db_path)], input="n\n")

        assert result.exit_code == 1
        assert db_path.exists()
        assert "Cancelled" in result.output

    def test_should_skip_confirmation_with_yes_flag(self, tmp_path):
        db_path = tmp_path / "cache.db"
        Cache(db_path).store_prs([any_pr(number=1)], "myorg", "myrepo", 2026, 4)

        result = runner.invoke(app, ["clear", "--db", str(db_path), "--yes"])

        assert result.exit_code == 0, result.output
        assert not db_path.exists()

    def test_should_no_op_when_cache_already_empty(self, tmp_path):
        db_path = tmp_path / "cache.db"
        assert not db_path.exists()

        result = runner.invoke(app, ["clear", "--db", str(db_path)])

        assert result.exit_code == 0, result.output
        assert "already empty" in result.output
        assert not db_path.exists()

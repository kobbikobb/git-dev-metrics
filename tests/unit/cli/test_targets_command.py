from typer.testing import CliRunner

from git_dev_metrics.cache import get_targets, set_target
from git_dev_metrics.cli import app

runner = CliRunner()


class TestTargetsCommand:
    def test_should_set_target_via_prompt(self, tmp_path):
        db_path = tmp_path / "cache.db"

        result = runner.invoke(
            app,
            ["targets", "--db", str(db_path)],
            input="24\n4\n12\n80\n2\n7\n5\n14\n21\n",
        )

        assert result.exit_code == 0, result.output
        targets = get_targets(db_path=db_path)
        assert targets["cycle_time_max"] == 24.0
        assert targets["health_min"] == 80.0
        assert targets["stale_threshold_days"] == 7.0

    def test_should_replace_existing_target(self, tmp_path):
        db_path = tmp_path / "cache.db"
        set_target("cycle_time_max", 48.0, db_path=db_path)

        result = runner.invoke(
            app,
            ["targets", "--db", str(db_path)],
            input="24\n\n\n\n\n\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert get_targets(db_path=db_path)["cycle_time_max"] == 24.0

    def test_should_clear_target_with_x(self, tmp_path):
        db_path = tmp_path / "cache.db"
        set_target("cycle_time_max", 24.0, db_path=db_path)

        result = runner.invoke(
            app,
            ["targets", "--db", str(db_path)],
            input="x\n\n\n\n\n\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert "cycle_time_max" not in get_targets(db_path=db_path)

    def test_should_skip_on_blank_input(self, tmp_path):
        db_path = tmp_path / "cache.db"
        set_target("cycle_time_max", 24.0, db_path=db_path)

        result = runner.invoke(
            app,
            ["targets", "--db", str(db_path)],
            input="\n\n\n\n\n\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert get_targets(db_path=db_path)["cycle_time_max"] == 24.0

    def test_should_show_current_values_as_hint(self, tmp_path):
        db_path = tmp_path / "cache.db"
        set_target("cycle_time_max", 24.0, db_path=db_path)

        result = runner.invoke(
            app,
            ["targets", "--db", str(db_path)],
            input="\n\n\n\n\n\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert "24.0" in result.output

    def test_should_reject_invalid_number(self, tmp_path):
        db_path = tmp_path / "cache.db"

        result = runner.invoke(
            app,
            ["targets", "--db", str(db_path)],
            input="abc\n24\n\n\n\n\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert "Invalid number" in result.stderr
        # cycle_time_max should NOT have been set, so get_targets should not contain it
        targets = get_targets(db_path=db_path)
        assert "cycle_time_max" not in targets

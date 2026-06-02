from typer.testing import CliRunner

from git_dev_metrics.cache import (
    get_nicknames,
    insert_prs,
    set_nickname,
)
from git_dev_metrics.cli import app

from ..conftest import any_pr, approved_review, dt

runner = CliRunner()


def _seed_four_devs(db_path) -> None:
    """April 2026 PRs with 4 unique devs across authors + reviewers."""
    prs = [
        any_pr(
            number=1,
            user={"login": "alice"},
            reviews=[approved_review(login="bob")],
            created_at=dt(year=2026, month=4, day=1, hour=9, minute=0),
            merged_at=dt(year=2026, month=4, day=2, hour=10, minute=0),
        ),
        any_pr(
            number=2,
            user={"login": "carol"},
            reviews=[approved_review(login="dave")],
            created_at=dt(year=2026, month=4, day=3, hour=9, minute=0),
            merged_at=dt(year=2026, month=4, day=4, hour=10, minute=0),
        ),
    ]
    insert_prs(prs, "myorg", "myrepo", 2026, 4, db_path=db_path)


class TestNicknameCommand:
    def test_should_exit_when_no_cached_data(self, tmp_path):
        db_path = tmp_path / "cache.db"

        result = runner.invoke(app, ["nickname", "--db", str(db_path)], input="")

        assert result.exit_code == 1
        assert "No cached data found" in result.stderr

    def test_should_set_nicknames_via_prompt(self, tmp_path):
        db_path = tmp_path / "cache.db"
        _seed_four_devs(db_path)

        result = runner.invoke(
            app,
            ["nickname", "--db", str(db_path)],
            input="Alpha\nBeta\nCharlie\nDave\n",
        )

        assert result.exit_code == 0, result.output
        assert get_nicknames(db_path=db_path) == {
            "alice": "Alpha",
            "bob": "Beta",
            "carol": "Charlie",
            "dave": "Dave",
        }

    def test_should_replace_existing_nickname(self, tmp_path):
        db_path = tmp_path / "cache.db"
        _seed_four_devs(db_path)
        set_nickname("alice", "OldName", db_path=db_path)

        result = runner.invoke(
            app,
            ["nickname", "--db", str(db_path)],
            input="NewName\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert get_nicknames(db_path=db_path)["alice"] == "NewName"

    def test_should_clear_nickname_with_x(self, tmp_path):
        db_path = tmp_path / "cache.db"
        _seed_four_devs(db_path)
        set_nickname("alice", "Alpha", db_path=db_path)
        set_nickname("bob", "Beta", db_path=db_path)

        result = runner.invoke(
            app,
            ["nickname", "--db", str(db_path)],
            input="x\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        nicknames = get_nicknames(db_path=db_path)
        assert "alice" not in nicknames
        assert nicknames["bob"] == "Beta"

    def test_should_skip_on_blank_input(self, tmp_path):
        db_path = tmp_path / "cache.db"
        _seed_four_devs(db_path)
        set_nickname("alice", "Alpha", db_path=db_path)

        result = runner.invoke(
            app,
            ["nickname", "--db", str(db_path)],
            input="\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert get_nicknames(db_path=db_path)["alice"] == "Alpha"

    def test_should_print_current_nicknames(self, tmp_path):
        db_path = tmp_path / "cache.db"
        _seed_four_devs(db_path)
        set_nickname("alice", "Alpha", db_path=db_path)

        result = runner.invoke(
            app,
            ["nickname", "--db", str(db_path)],
            input="\n\n\n\n",
        )

        assert result.exit_code == 0, result.output
        assert "alice → Alpha" in result.output

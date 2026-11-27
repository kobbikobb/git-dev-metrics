from pathlib import Path

from typer.testing import CliRunner

from git_dev_metrics.cache import (
    get_all_dev_logins,
    get_hidden_logins,
    insert_prs,
    set_nickname,
)
from git_dev_metrics.cli import app

from ..conftest import any_pr, approved_review

runner = CliRunner()


def _seed(db_path: Path) -> None:
    pr = any_pr(user={"login": "Dev-A"}, reviews=[approved_review(login="dev-b")])
    insert_prs([pr], "org", "repo", 2026, 4, db_path=db_path)


class TestHideCommand:
    def test_should_hide_and_restore_cached_authors_and_reviewers(self, tmp_path: Path) -> None:
        db = tmp_path / "cache.db"
        _seed(db)
        set_nickname("Dev-A", "Alias A", db_path=db)
        command = ["hide", "--db", str(db)]

        result = runner.invoke(app, command, input="y\ny\n")

        assert result.exit_code == 0, result.output
        assert "dev-a (Alias A)" in result.output
        assert get_hidden_logins(db) == {"dev-a", "dev-b"}
        assert get_all_dev_logins(db) == {"Dev-A", "dev-b"}

        result = runner.invoke(app, command, input="\nn\n")

        assert result.exit_code == 0, result.output
        assert "currently hidden" in result.output
        assert get_hidden_logins(db) == {"dev-a"}
        assert get_hidden_logins(tmp_path / "separate.db") == set()

    def test_should_keep_prior_settings_when_interrupted(self, tmp_path: Path) -> None:
        db = tmp_path / "cache.db"
        _seed(db)

        result = runner.invoke(app, ["hide", "--db", str(db)], input="y\n")

        assert result.exit_code != 0
        assert not get_hidden_logins(db)

    def test_should_explain_when_there_are_no_cached_developers(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["hide", "--db", str(tmp_path / "cache.db")])

        assert result.exit_code == 1
        assert "Pull some months first" in result.stderr

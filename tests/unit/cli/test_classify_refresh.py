import json
import sqlite3
from pathlib import Path

import responses
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, open_connection
from git_dev_metrics.classification import classify_pending
from git_dev_metrics.cli import app

from ..conftest import any_pr
from .test_classify_command import SHOW, URL


def _reply(*labels: str) -> None:
    predictions = {str(i): label for i, label in enumerate(labels)}
    responses.post(URL, json={"message": {"content": json.dumps(predictions)}})


class TestClassifyRefresh:
    @responses.activate
    def test_should_resume_only_unfinished_prs_after_failed_refresh(self, tmp_path: Path) -> None:
        db = tmp_path / "refresh.db"
        args = ["classify", "--db", str(db)]
        cli = CliRunner()
        prs = [any_pr(number=i) for i in range(5)]
        insert_prs(prs, "org", "repo", 2026, 1, db)
        insert_prs(prs, "ORG", "Repo", 2026, 2, db)
        insert_prs([any_pr(number=5, merged_at=None)], "org", "repo", 2026, 1, db)
        conn = open_connection(db)
        with conn:
            conn.executemany(
                "INSERT INTO pr_classifications VALUES ('org','repo',?,'maintenance','old','ci')",
                [(i,) for i in range(5)],
            )
        responses.post(SHOW, json={"model_info": {"name": "test"}})
        _reply(*["enhancement"] * 4)
        _reply("invalid")

        failed = cli.invoke(app, [*args, "--force"])

        assert failed.exit_code == 1
        assert "4 of 5" in failed.output
        query = "SELECT subcategory FROM pr_classifications ORDER BY number"
        assert [r[0] for r in conn.execute(query)] == ["enhancement"] * 4 + ["ci"]
        assert "Classified 0" in cli.invoke(app, args).output
        insert_prs([any_pr(number=6)], "org", "repo", 2026, 1, db)
        _reply("tooling")
        assert "Classified 1 " in cli.invoke(app, [*args, "--force"]).output
        assert [r[0] for r in conn.execute(query)] == ["enhancement"] * 4 + ["tooling"]
        assert "Classified 1 " in cli.invoke(app, args).output

    @responses.activate
    def test_should_ignore_inflight_result_from_finished_refresh(self, tmp_path: Path) -> None:
        db = tmp_path / "refresh.db"
        insert_prs([any_pr(number=i) for i in (1, 2)], "org", "repo", 2026, 1, db)
        responses.post(SHOW, json={"model_info": {"name": "test"}})
        _reply("dependency", "ci")
        _reply("tooling")
        _reply("bug_fix", "bug_fix")
        _reply("security_update")

        def another_worker(done: int, total: int) -> None:
            if done == 0:
                with sqlite3.connect(db) as other:
                    other.row_factory = sqlite3.Row
                    classify_pending(other, "local", None, lambda *_: None, force=True)
                    classify_pending(other, "local", 1, lambda *_: None, force=True)

        conn = open_connection(db)
        stale = classify_pending(conn, "old", None, another_worker, force=True)
        resumed = classify_pending(conn, "new", None, lambda *_: None, force=True)

        assert not stale
        assert resumed == {"security_update": 1}
        rows = conn.execute("SELECT subcategory, model FROM pr_classifications ORDER BY number")
        assert [tuple(row) for row in rows] == [("tooling", "local"), ("security_update", "new")]

    @responses.activate
    def test_should_start_a_fresh_pass_when_remaining_pr_disappears(self, tmp_path: Path) -> None:
        db = tmp_path / "refresh.db"
        insert_prs([any_pr(number=i) for i in (1, 2)], "org", "repo", 2026, 1, db)
        conn = open_connection(db)
        responses.post(SHOW, json={"model_info": {"name": "test"}})
        _reply("ci")
        _reply("refactoring")

        classify_pending(conn, "local", 1, lambda *_: None, force=True)
        with conn:
            conn.execute("DELETE FROM prs WHERE number = 2")
        result = classify_pending(conn, "local", None, lambda *_: None, force=True)

        assert result == {"refactoring": 1}

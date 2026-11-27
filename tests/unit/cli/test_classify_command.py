import json
import sqlite3
from pathlib import Path

import pytest
import responses
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, open_connection
from git_dev_metrics.classification import BATCH_SIZE, classify_pending
from git_dev_metrics.cli import app
from git_dev_metrics.cli.commands.classify import _timed_progress

from ..conftest import any_pr

SHOW = "http://127.0.0.1:11434/api/show"
URL = "http://127.0.0.1:11434/api/chat"
runner = CliRunner()


class TestClassify:
    @responses.activate
    def test_should_classify_merged_prs_once_across_repos_and_repulls(self, tmp_path: Path) -> None:
        responses.post(SHOW, json={"model_info": {"general.architecture": "test"}})
        db = tmp_path / "cache.db"
        args = ["classify", "--db", str(db), "--model", "local"]
        for repo in ("first", "second"):
            insert_prs(
                [any_pr(number=2), any_pr(number=3, merged_at=None)], "org", repo, 2026, 1, db
            )
        responses.post(URL, json={"message": {"content": '{"0":"tooling"}'}})

        limited = runner.invoke(app, [*args, "--limit", "1"])
        assert limited.exit_code == 0
        assert "1 of 1" in limited.output
        insert_prs([any_pr(number=2)], "org", "first", 2026, 1, db)
        assert runner.invoke(app, args).exit_code == 0
        assert "Classified 0" in runner.invoke(app, args).output

        assert len(responses.calls) == 4
        rows = open_connection(db).execute(
            "SELECT repo_name, number, category, model, subcategory FROM pr_classifications "
            "ORDER BY repo_name"
        )
        assert [tuple(row) for row in rows] == [
            ("first", 2, "maintenance", "local", "tooling"),
            ("second", 2, "maintenance", "local", "tooling"),
        ]

    @responses.activate
    def test_should_replace_legacy_labels_only_after_valid_prediction(self, tmp_path: Path) -> None:
        db = tmp_path / "cache.db"
        with sqlite3.connect(db) as old:
            old.execute("""CREATE TABLE pr_classifications (
                repo_org TEXT COLLATE NOCASE, repo_name TEXT COLLATE NOCASE, number INTEGER,
                category TEXT, model TEXT, PRIMARY KEY (repo_org, repo_name, number))""")
            old.execute("INSERT INTO pr_classifications VALUES ('ORG','REPO',1,'unclear','old')")
        insert_prs([any_pr(number=1)], "org", "repo", 2026, 1, db)
        args = ["classify", "--db", str(db), "--model", "local"]
        responses.post(SHOW, json={"model_info": {"name": "test"}})
        responses.post(URL, json={"message": {"content": "{}"}})
        conn = open_connection(db)
        query = "SELECT category, model, subcategory FROM pr_classifications"

        assert runner.invoke(app, args).exit_code == 1
        assert tuple(conn.execute(query).fetchone()) == ("unclear", "old", None)
        responses.replace(responses.POST, URL, json={"message": {"content": '{"0":"ci"}'}})
        assert "Classified 1" in runner.invoke(app, args).output
        assert "Classified 0" in runner.invoke(app, args).output
        assert tuple(conn.execute(query).fetchone()) == ("maintenance", "local", "ci")

    @pytest.mark.parametrize("invalid", ["{}", '{"0":"feature"}', '{"0":"invalid"}', "truncated"])
    @responses.activate
    def test_should_resume_after_rejecting_an_invalid_batch(
        self, tmp_path: Path, invalid: str
    ) -> None:
        responses.post(SHOW, json={"model_info": {"general.architecture": "test"}})
        db = tmp_path / "cache.db"
        args = ["classify", "--db", str(db)]
        prs = [any_pr(number=n) for n in range(BATCH_SIZE + 1)]
        insert_prs(prs, "org", "repo", 2026, 1, db)
        complete = {str(i): "new_capability" for i in range(BATCH_SIZE)}
        responses.post(URL, json={"message": {"content": json.dumps(complete)}})
        responses.post(URL, json={"message": {"content": invalid}})

        result = runner.invoke(app, args)
        assert result.exit_code == 1
        assert f"0 of {len(prs)}" in result.output
        assert f"{BATCH_SIZE} of {len(prs)}" in result.output
        assert f"{len(prs)} of {len(prs)}" not in result.output
        responses.replace(responses.POST, URL, json={"message": {"content": '{"0":"unclear"}'}})
        assert "Classified 1 " in runner.invoke(app, args).output
        assert "Classified 0 " in runner.invoke(app, args).output

    @responses.activate
    def test_should_refuse_remote_model_before_sending_pr_text(self, tmp_path: Path) -> None:
        db = tmp_path / "cache.db"
        insert_prs([any_pr()], "org", "repo", 2026, 1, db)
        responses.post(SHOW, json={"model_info": {"name": "test"}, "remote_model": "cloud"})

        result = runner.invoke(app, ["classify", "--db", str(db)])

        assert result.exit_code == 1
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == SHOW

    @responses.activate
    def test_should_match_categories_by_response_key(self, tmp_path: Path) -> None:
        db = tmp_path / "cache.db"
        insert_prs([any_pr(number=8), any_pr(number=9)], "org", "repo", 2026, 1, db)
        responses.post(SHOW, json={"model_info": {"general.architecture": "test"}})
        responses.post(URL, json={"message": {"content": '{"1":"enhancement","0":"bug_fix"}'}})

        assert runner.invoke(app, ["classify", "--db", str(db)]).exit_code == 0

        rows = open_connection(db).execute(
            "SELECT number, category, subcategory FROM pr_classifications ORDER BY number"
        )
        assert [tuple(row) for row in rows] == [
            (8, "maintenance", "bug_fix"),
            (9, "feature", "enhancement"),
        ]

    @responses.activate
    def test_should_finish_progress_when_another_run_drains_the_queue(self, tmp_path: Path) -> None:
        db = tmp_path / "cache.db"
        insert_prs([any_pr(number=n) for n in range(257)], "org", "repo", 2026, 1, db)
        responses.post(SHOW, json={"model_info": {"general.architecture": "test"}})
        labels = json.dumps({str(i): "new_capability" for i in range(BATCH_SIZE)})
        responses.post(URL, json={"message": {"content": labels}})
        updates: list[tuple[int, int]] = []

        def progress(done: int, total: int) -> None:
            updates.append((done, total))
            if done == BATCH_SIZE:
                with sqlite3.connect(db) as other:
                    other.execute(
                        "INSERT INTO pr_classifications "
                        "VALUES ('org', 'repo', 256, 'unclear', 'm', 'unclear')"
                    )

        counts = classify_pending(open_connection(db), "local", None, progress)

        assert updates[-1] == (257, 257)
        assert counts == {"new_capability": 256}

    def test_should_estimate_time_from_saved_prs(self, capsys: pytest.CaptureFixture[str]) -> None:
        now = 100.0
        with _timed_progress(clock=lambda: now) as progress:
            progress(0, 10)
            now += 6
            progress(4, 10)
            now += 7
            progress(10, 10)

        lines = capsys.readouterr().err.splitlines()
        assert lines == [
            "Classifying PRs: 0 of 10 | elapsed 0:00:00 | time left estimating",
            "Classifying PRs: 4 of 10 | elapsed 0:00:06 | time left 0:00:09",
            "Classifying PRs: 10 of 10 | elapsed 0:00:13 | time left 0:00:00",
        ]

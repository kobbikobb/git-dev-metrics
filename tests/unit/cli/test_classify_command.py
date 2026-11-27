import json
from pathlib import Path

import pytest
import responses
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, open_connection
from git_dev_metrics.classification import BATCH_SIZE
from git_dev_metrics.cli import app

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
        responses.post(URL, json={"message": {"content": '{"0":"maintenance"}'}})

        assert runner.invoke(app, [*args, "--limit", "1"]).exit_code == 0
        insert_prs([any_pr(number=2)], "org", "first", 2026, 1, db)
        assert runner.invoke(app, args).exit_code == 0
        assert "Classified 0" in runner.invoke(app, args).output

        assert len(responses.calls) == 4
        rows = open_connection(db).execute(
            "SELECT repo_name, number, category, model FROM pr_classifications ORDER BY repo_name"
        )
        assert [tuple(row) for row in rows] == [
            ("first", 2, "maintenance", "local"),
            ("second", 2, "maintenance", "local"),
        ]

    @pytest.mark.parametrize("invalid", ["{}", '{"0":"invalid"}', "truncated"])
    @responses.activate
    def test_should_resume_after_rejecting_an_invalid_batch(
        self, tmp_path: Path, invalid: str
    ) -> None:
        responses.post(SHOW, json={"model_info": {"general.architecture": "test"}})
        db = tmp_path / "cache.db"
        args = ["classify", "--db", str(db)]
        prs = [any_pr(number=n) for n in range(BATCH_SIZE + 1)]
        insert_prs(prs, "org", "repo", 2026, 1, db)
        complete = {str(i): "feature" for i in range(BATCH_SIZE)}
        responses.post(URL, json={"message": {"content": json.dumps(complete)}})
        responses.post(URL, json={"message": {"content": invalid}})

        assert runner.invoke(app, args).exit_code == 1
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
        responses.post(URL, json={"message": {"content": '{"1":"feature","0":"bug_fix"}'}})

        assert runner.invoke(app, ["classify", "--db", str(db)]).exit_code == 0

        rows = open_connection(db).execute(
            "SELECT number, category FROM pr_classifications ORDER BY number"
        )
        assert [tuple(row) for row in rows] == [(8, "bug_fix"), (9, "feature")]

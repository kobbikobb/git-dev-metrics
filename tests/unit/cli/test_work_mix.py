import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, mark_partial, open_connection, seal_month
from git_dev_metrics.cli import app

from ..conftest import any_pr


class TestWorkMix:
    @pytest.mark.parametrize(("filters", "pending"), [([], 3), (["--repo", "Org/One"], 1)])
    def test_should_render_counts_by_merge_month_and_preserve_coverage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filters: list[str], pending: int
    ) -> None:
        db = tmp_path / "cache.db"
        for repo in ("one", "two"):
            mark_partial("org", repo, 2026, 1, db)
            seal_month("org", repo, 2026, 3, db)
            prs = [any_pr(number=n, merged_at=datetime(2026, 1, 1, tzinfo=UTC)) for n in (1, 2)]
            insert_prs(prs, "org", repo, 2026, 1, db)
            insert_prs(prs, "ORG", repo, 2026, 2, db)
        seal_month("org", "one", 2026, 4, db)
        with open_connection(db) as conn:
            conn.execute("INSERT INTO pr_classifications VALUES ('ORG','one',1,'unclear','local')")
        output = tmp_path / "report.html"
        monkeypatch.setattr("webbrowser.open", lambda *_: True)
        args = ["--from", "2026-01", "--to", "2026-04", *filters]

        result = CliRunner().invoke(
            app, ["work-mix", *args, "--db", str(db), "--output", str(output)]
        )

        assert result.exit_code == 0, result.output
        html = output.read_text()
        data = json.loads(html.split("const mix = ")[1].split(";\n")[0])
        assert data == {
            "2026-01": {"partial": True, "counts": {"unclear": 1, "unclassified": pending}},
            "2026-03": {"partial": False, "counts": {}},
            "2026-04": {"partial": not filters, "counts": {}},
        }

    def test_should_explain_empty_cache(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["work-mix", "--db", str(tmp_path / "empty.db")])

        assert result.exit_code != 0
        assert "Run pull first" in result.output

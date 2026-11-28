import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, mark_partial, open_connection, seal_month
from git_dev_metrics.cli import app

from ..conftest import any_pr


class TestWorkMix:
    @pytest.mark.parametrize(("filters", "pending"), [([], 3), (["--repo", "Org/One"], 0)])
    def test_should_render_counts_by_merge_month_and_preserve_coverage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filters: list[str], pending: int
    ) -> None:
        db = tmp_path / "cache.db"
        for repo in ("one", "two"):
            mark_partial("org", repo, 2026, 1, db)
            seal_month("org", repo, 2026, 3, db)
            prs = [
                any_pr(number=n, merged_at=datetime(2026, 1, 1, tzinfo=UTC)) for n in range(1, 7)
            ]
            insert_prs(prs, "org", repo, 2026, 1, db)
            insert_prs(prs, "ORG", repo, 2026, 2, db)
        seal_month("org", "one", 2026, 4, db)
        with open_connection(db) as conn:
            conn.executemany(
                "INSERT INTO pr_classifications "
                "(repo_org, repo_name, number, category, subcategory, model) "
                "VALUES ('ORG',?,?,?,?,'local')",
                [
                    ("one", 1, "unclear", "unclear"),
                    ("one", 2, "bug_fix", None),
                    ("one", 3, "maintenance", "dependency"),
                    ("one", 4, "maintenance", None),
                    ("one", 5, "feature", None),
                    ("one", 6, "feature", "enhancement"),
                    ("two", 1, "maintenance", "dependency"),
                    ("two", 2, "maintenance", "bug_fix"),
                    ("two", 3, "feature", "new_capability"),
                ],
            )
        output = tmp_path / "report.html"
        monkeypatch.setattr("webbrowser.open", lambda *_: True)
        args = ["--from", "2026-01", "--to", "2026-04", *filters]

        result = CliRunner().invoke(
            app, ["work-mix", *args, "--db", str(db), "--output", str(output)]
        )

        assert result.exit_code == 0, result.output
        html = output.read_text()
        assert html.count("<canvas ") == 3
        assert "<h2>Maintenance breakdown</h2>" in html
        assert "<h2>Feature work breakdown</h2>" in html
        assert "Share of merged PRs" not in html
        data = json.loads(html.split("const mix = ")[1].split(";\n")[0])
        assert data == {
            "2026-01": {
                "partial": True,
                "counts": {
                    "unclear": 1,
                    "maintenance": 3 if filters else 5,
                    "feature": 2 if filters else 3,
                    **({"unclassified": pending} if pending else {}),
                },
                "subcategories": {
                    "bug_fix": 1 if filters else 2,
                    "dependency": 1 if filters else 2,
                    "maintenance_unspecified": 1,
                    "feature_unspecified": 1,
                    "enhancement": 1,
                    **({} if filters else {"new_capability": 1}),
                },
            },
            "2026-03": {"partial": False, "counts": {}, "subcategories": {}},
            "2026-04": {"partial": not filters, "counts": {}, "subcategories": {}},
        }

    def test_should_explain_empty_cache(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["work-mix", "--db", str(tmp_path / "empty.db")])

        assert result.exit_code != 0
        assert "Run pull first" in result.output

    def test_should_keep_repository_scope_stable_across_date_ranges(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db = tmp_path / "cache.db"
        seal_month("org", "one", 2026, 1, db)
        seal_month("org", "two", 2026, 2, db)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("webbrowser.open", lambda *_: True)
        args = ["work-mix", "--from", "2026-01", "--to", "2026-01", "--db", str(db)]

        for filters in ([], ["--repo", "org/one"]):
            assert CliRunner().invoke(app, [*args, *filters]).exit_code == 0

        reports = sorted(Path("metrics_results").glob("*.html"))
        assert len(reports) == 2
        for path in reports:
            html = path.read_text()
            data = json.loads(html.split("const mix = ")[1].split(";\n")[0])
            assert data["2026-01"]["partial"] == ("2 synced repositories" in html)
        assert "org/one" in reports[1].read_text()

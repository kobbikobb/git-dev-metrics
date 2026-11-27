from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, seal_month, set_nickname, update_hidden_logins
from git_dev_metrics.cli import app
from git_dev_metrics.metrics._stale_pr import StalePr
from git_dev_metrics.metrics.printer.lang import FileLangPrinter
from git_dev_metrics.metrics.printer.skill import FileSkillPrinter
from git_dev_metrics.metrics.printer.stale import FileStaleHtmlPrinter
from git_dev_metrics.metrics.report_data import ReportData

from ..conftest import any_pr


class TestReportVisibility:
    @pytest.mark.parametrize("report", ["skill", "lang"])
    def test_should_keep_team_breakdown_when_all_devs_are_hidden(
        self, tmp_path: Path, report: str
    ) -> None:
        prs = [{"user": {"login": "Dev-A"}, "files": [{"path": "main.py"}]}]
        output = tmp_path / "report.html"

        db = tmp_path / "cache.db"
        update_hidden_logins({"dev-a": True}, db_path=db)
        data = ReportData(db)
        if report == "lang":
            FileLangPrinter(output).render(data.languages(prs), "June")
        else:
            FileSkillPrinter(output).render(data.skills(prs), "June")

        html = output.read_text()
        assert "Dev-A" not in html
        assert 'const TEAM = {"Python": 1}' in html
        assert "const DEVS = []" in html

    @pytest.mark.parametrize("report", ["skill", "lang"])
    def test_should_count_same_number_in_different_repos(
        self, tmp_path: Path, report: str, mocker, _stub_webbrowser
    ) -> None:
        db = tmp_path / "cache.db"
        out = tmp_path / "report.html"
        for repo in ("repo-a", "repo-b"):
            seal_month("org", repo, 2026, 6, db_path=db)
        seal_month("org", "repo-a", 2026, 7, db_path=db)
        update_hidden_logins({"dev-a": True}, db_path=db)
        mocker.patch("git_dev_metrics.cli.runners._report_prs.load_token", return_value="test")

        set_nickname("dev-b", "Alias B", db_path=db)

        def fetch(token: str, org: str, repo: str, year: int, month: int) -> list[dict]:
            login = {"repo-a": "Dev-A", "repo-b": "Dev-B"}[repo]
            return [{"number": 1, "user": {"login": login}, "files": [{"path": "main.py"}]}]

        mocker.patch(
            f"git_dev_metrics.cli.runners._report_prs.fetch_{report}_report_prs",
            side_effect=fetch,
        )
        args = ["--from", "2026-06", "--to", "2026-07", "--db", str(db), "--output", str(out)]

        result = CliRunner().invoke(app, [f"{report}-report", *args])

        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert 'const TEAM = {"Python": 2}' in html
        assert '"label": "Alias B"' in html
        assert "Dev-B" not in html
        assert "Dev-A" not in html

    @pytest.mark.parametrize("report", ["trend", "team-velocity"])
    def test_should_keep_visible_series_separate_with_shared_nicknames(
        self, tmp_path: Path, report: str, mocker, _stub_webbrowser
    ) -> None:
        db = tmp_path / "cache.db"
        out = tmp_path / "velocity.html"
        prs = [
            any_pr(number=i, user={"login": name})
            for i, name in enumerate(("Dev-A", "Dev-B", "Dev-C", "Dev-D", "Dev-D"), 1)
        ]
        insert_prs(prs, "org", "repo", 2026, 6, db_path=db)
        seal_month("org", "repo", 2026, 6, db_path=db)
        update_hidden_logins({"dev-a": True}, db_path=db)
        set_nickname("dev-a", "Hidden alias", db_path=db)
        set_nickname("dev-b", "Visible alias", db_path=db)
        set_nickname("DEV-D", "Visible alias", db_path=db)
        mocker.patch(
            "git_dev_metrics.cli.commands.team_velocity.last_n_months",
            return_value=((2026, 6), (2026, 6)),
        )

        args = ["--from", "2026-06", "--to", "2026-06"] if report == "trend" else []
        result = CliRunner().invoke(app, [report, *args, "--db", str(db), "--output", str(out)])

        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "Dev-A" not in html
        assert "Hidden alias" not in html
        assert "Dev-B" not in html
        assert html.count('"label": "Visible alias"') == 2
        assert "Dev-D" not in html
        assert '"label": "Dev-C"' in html
        if report == "team-velocity":
            assert html.index("<td>Visible alias</td><td>2</td>") < html.index(
                "<td>Visible alias</td><td>1</td>"
            )
            assert "const ACTIVE_DEVS = [4]" in html
            assert "const PR_COUNTS = [5]" in html

    def test_should_show_stale_pr_without_hidden_author(self, tmp_path: Path) -> None:
        pr = StalePr(42, "Pending review", "Dev-A", "org/repo", 240, 10, False, False, "")
        output = tmp_path / "report.html"

        db = tmp_path / "cache.db"
        update_hidden_logins({"dev-a": True}, db_path=db)
        FileStaleHtmlPrinter(output).render(ReportData(db).stale([pr]))

        html = output.read_text()
        assert "Dev-A" not in html
        assert "Pending review" in html
        assert "<td>—</td>" in html

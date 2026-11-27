from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, seal_month, update_hidden_logins
from git_dev_metrics.cli import app
from git_dev_metrics.metrics._stale_pr import StalePr
from git_dev_metrics.metrics.lang_calculator import build_lang_dataset
from git_dev_metrics.metrics.printer.lang import FileLangPrinter
from git_dev_metrics.metrics.printer.skill import FileSkillPrinter
from git_dev_metrics.metrics.printer.stale import FileStaleHtmlPrinter
from git_dev_metrics.metrics.printer.trend import FileTrendPrinter
from git_dev_metrics.metrics.skill_calculator import build_skill_dataset
from git_dev_metrics.metrics.trend_calculator import build_trend_dataset

from ..conftest import any_pr


class TestReportVisibility:
    @pytest.mark.parametrize("report", ["skill", "lang"])
    def test_should_keep_team_breakdown_when_all_devs_are_hidden(
        self, tmp_path: Path, report: str
    ) -> None:
        prs = [{"user": {"login": "Dev-A"}, "files": [{"path": "main.py"}]}]
        output = tmp_path / "report.html"

        if report == "lang":
            FileLangPrinter(output).render(build_lang_dataset(prs), "June", hidden_logins={"dev-a"})
        else:
            FileSkillPrinter(output).render(
                build_skill_dataset(prs), "June", hidden_logins={"dev-a"}
            )

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

        def fetch(token: str, org: str, repo: str, year: int, month: int) -> list[dict]:
            login = {"repo-a": "Dev-A", "repo-b": "Dev-B"}[repo]
            return [{"number": 1, "user": {"login": login}, "files": [{"path": "main.py"}]}]

        mocker.patch(
            f"git_dev_metrics.cli.runners.{report}_runner.fetch_{report}_report_prs",
            side_effect=fetch,
        )
        args = ["--from", "2026-06", "--to", "2026-07", "--db", str(db), "--output", str(out)]

        result = CliRunner().invoke(app, [f"{report}-report", *args])

        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert 'const TEAM = {"Python": 2}' in html
        assert 'const DEVS = ["Dev-B"]' in html
        assert "Dev-A" not in html

    def test_should_hide_named_trend_series(self, tmp_path: Path) -> None:
        months = [(2026, 6)]
        activity = {months[0]: [any_pr(user={"login": "Dev-A"}), any_pr(user={"login": "Dev-B"})]}
        trend = tmp_path / "trend.html"

        FileTrendPrinter(trend).render(
            build_trend_dataset(months, activity), hidden_logins={"dev-a"}
        )

        html = trend.read_text()
        assert "Dev-A" not in html
        assert "Dev-B" in html

    def test_should_keep_team_velocity_for_developers_hidden_in_selected_db(
        self, tmp_path: Path, mocker, _stub_webbrowser
    ) -> None:
        db = tmp_path / "cache.db"
        out = tmp_path / "velocity.html"
        prs = [
            any_pr(number=i, user={"login": name}) for i, name in enumerate(("Dev-A", "Dev-B"), 1)
        ]
        insert_prs(prs, "org", "repo", 2026, 6, db_path=db)
        seal_month("org", "repo", 2026, 6, db_path=db)
        update_hidden_logins({"dev-a": True}, db_path=db)
        mocker.patch(
            "git_dev_metrics.cli.commands.team_velocity.last_n_months",
            return_value=((2026, 6), (2026, 6)),
        )

        result = CliRunner().invoke(app, ["team-velocity", "--db", str(db), "--output", str(out)])

        assert result.exit_code == 0, result.output
        html = out.read_text()
        assert "Dev-A" not in html
        assert "Dev-B" in html
        assert "const ACTIVE_DEVS = [2]" in html
        assert "const PR_COUNTS = [2]" in html

    def test_should_show_stale_pr_without_hidden_author(self, tmp_path: Path) -> None:
        pr = StalePr(42, "Pending review", "Dev-A", "org/repo", 240, 10, False, False, "")
        output = tmp_path / "report.html"

        FileStaleHtmlPrinter(output).render([pr], hidden_logins={"dev-a"})

        html = output.read_text()
        assert "Dev-A" not in html
        assert "Pending review" in html
        assert "<td>—</td>" in html

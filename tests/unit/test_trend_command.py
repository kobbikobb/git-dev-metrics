import json
import re

from freezegun import freeze_time
from typer.testing import CliRunner

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli.app import app
from git_dev_metrics.cli.trend_wizard import trend_wizard
from git_dev_metrics.models import PullRequest

from .conftest import any_pr, approved_review

runner = CliRunner()


def _pr(pr_id: int, login: str, year: int, month: int, day: int) -> PullRequest:
    return any_pr(
        id=pr_id,
        number=pr_id,
        user={"login": login},
        created_at=f"{year:04d}-{month:02d}-{day:02d}T08:00:00Z",
        merged_at=f"{year:04d}-{month:02d}-{day:02d}T18:00:00Z",
        reviews=[approved_review(submitted_at=f"{year:04d}-{month:02d}-{day:02d}T12:00:00Z")],
    )


def _seed_three_months(db_path) -> None:
    feb = [
        _pr(1, "alice", 2026, 2, 5),
        _pr(2, "alice", 2026, 2, 12),
        _pr(3, "bob", 2026, 2, 7),
        _pr(4, "charlie", 2026, 2, 9),
        _pr(5, "charlie", 2026, 2, 11),
        _pr(6, "charlie", 2026, 2, 19),
    ]
    mar = [
        _pr(7, "alice", 2026, 3, 4),
        _pr(8, "bob", 2026, 3, 10),
        _pr(9, "bob", 2026, 3, 21),
    ]
    apr = [
        _pr(10, "alice", 2026, 4, 3),
        _pr(11, "alice", 2026, 4, 11),
        _pr(12, "alice", 2026, 4, 22),
        _pr(13, "bob", 2026, 4, 8),
        _pr(14, "bob", 2026, 4, 18),
    ]
    insert_prs(feb, "myorg", "myrepo", 2026, 2, db_path=db_path)
    insert_prs(mar, "myorg", "myrepo", 2026, 3, db_path=db_path)
    insert_prs(apr, "myorg", "myrepo", 2026, 4, db_path=db_path)
    seal_month("myorg", "myrepo", 2026, 2, db_path=db_path)
    seal_month("myorg", "myrepo", 2026, 3, db_path=db_path)
    seal_month("myorg", "myrepo", 2026, 4, db_path=db_path)


def _data_block(html: str) -> dict:
    match = re.search(r"const DATA = (\{.*?\});", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


class TestTrendFiltersLeavers:
    @freeze_time("2026-05-12")
    def test_should_render_active_devs_only_and_omit_leavers(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_three_months(db_path)
        out = tmp_path / "t.html"

        # Act
        result = runner.invoke(
            app,
            [
                "trend",
                "--from",
                "2026-02",
                "--to",
                "2026-04",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
                "--output",
                str(out),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text()
        assert "alice" in content
        assert "bob" in content
        assert "charlie" not in content
        data = _data_block(content)
        assert "charlie" not in data["devs"]


class TestTrendCanvases:
    @freeze_time("2026-05-12")
    def test_should_render_three_chart_canvases_with_cdn(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_three_months(db_path)
        out = tmp_path / "t.html"

        # Act
        result = runner.invoke(
            app,
            [
                "trend",
                "--from",
                "2026-02",
                "--to",
                "2026-04",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
                "--output",
                str(out),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        content = out.read_text()
        assert "<canvas" in content
        assert 'id="prs"' in content
        assert 'id="cycle"' in content
        assert 'id="ai"' in content
        assert "Chart.js" in content or "chart.js" in content
        assert "cdn.jsdelivr.net" in content or "unpkg.com" in content


class TestTrendWizard:
    @freeze_time("2026-05-12")
    def test_should_render_default_output_from_wizard_picks(self, tmp_path, monkeypatch):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_three_months(db_path)
        monkeypatch.chdir(tmp_path)

        # Act
        trend_wizard(
            db_path=db_path,
            ask_repo_pick=lambda _repos: ("myorg", "myrepo"),
            ask_from=lambda _months: (2026, 2),
            ask_to=lambda _months: (2026, 4),
        )

        # Assert
        expected = tmp_path / "metrics_results" / "trend_myorg-myrepo_2026-02_2026-04.html"
        assert expected.exists()


class TestTrendCli:
    def test_should_invoke_wizard_when_no_flags(self, tmp_path, mocker):
        db_path = tmp_path / "cache.db"
        wizard = mocker.patch("git_dev_metrics.cli.trend.trend_wizard")

        result = runner.invoke(app, ["trend", "--db", str(db_path)])

        assert result.exit_code == 0, result.output
        wizard.assert_called_once_with(db_path=db_path)


class TestTrendRefusesUnsealed:
    @freeze_time("2026-05-12")
    def test_should_refuse_when_month_in_range_not_sealed(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "myrepo", 2026, 4, db_path=db_path)
        out = tmp_path / "t.html"

        # Act
        result = runner.invoke(
            app,
            [
                "trend",
                "--from",
                "2026-04",
                "--to",
                "2026-05",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
                "--output",
                str(out),
            ],
        )

        # Assert
        assert result.exit_code == 1
        assert "May 2026 not sealed" in result.stderr
        assert not out.exists()

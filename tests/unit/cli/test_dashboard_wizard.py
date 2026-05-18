from typer.testing import CliRunner

from git_dev_metrics.cache import Cache
from git_dev_metrics.cli.app import app

from ..conftest import any_pr, dt

runner = CliRunner()


def _seed_apr(cache: Cache) -> None:
    cache.store_prs(
        [
            any_pr(
                number=1,
                user={"login": "alice"},
                created_at=dt(year=2026, month=4, day=1, hour=8, minute=0),
                merged_at=dt(year=2026, month=4, day=2, hour=8, minute=0),
            )
        ],
        "myorg",
        "myrepo",
        2026,
        4,
    )
    cache.seal_month("myorg", "myrepo", 2026, 4)


class TestDashboardWizardRenders:
    def test_should_render_html_and_open_browser(self, tmp_path, mocker, _stub_webbrowser):
        mocker.patch(
            "git_dev_metrics.cli.wizards.dashboard_wizard._prompt_months",
            return_value=[(2026, 4)],
        )
        db_path = tmp_path / "cache.db"
        _seed_apr(Cache(db_path))

        result = runner.invoke(app, ["dashboard", "--db", str(db_path)])

        assert result.exit_code == 0, result.output


class TestDashboardWizardEmptyCache:
    def test_should_error_when_no_synced_months(self, tmp_path):
        db_path = tmp_path / "cache.db"

        result = runner.invoke(app, ["dashboard", "--db", str(db_path)])

        assert result.exit_code == 1
        assert "No synced months" in result.stderr


class TestDashboardWizardCancelled:
    def test_should_exit_when_user_picks_nothing(self, tmp_path, mocker):
        mocker.patch(
            "git_dev_metrics.cli.wizards.dashboard_wizard._prompt_months",
            return_value=[],
        )
        db_path = tmp_path / "cache.db"

        result = runner.invoke(app, ["dashboard", "--db", str(db_path)])

        assert result.exit_code == 1

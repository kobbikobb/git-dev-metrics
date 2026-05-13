import pytest
import typer

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli.dashboard_wizard import dashboard_wizard

from .conftest import any_pr, approved_review


def _seed_feb_mar_apr(db_path) -> None:
    for org, repo in (("myorg", "repoA"), ("myorg", "repoB")):
        for year, month, day in ((2026, 2, 5), (2026, 3, 7), (2026, 4, 9)):
            insert_prs(
                [
                    any_pr(
                        number=year * 100 + month, user={"login": "alice"},
                        additions=20, deletions=5, changed_files=2,
                        created_at=f"2026-{month:02d}-{day:02d}T08:00:00Z",
                        merged_at=f"2026-{month:02d}-{day:02d}T16:00:00Z",
                        closed_at=f"2026-{month:02d}-{day:02d}T16:00:00Z",
                        reviews=[approved_review(login="bob")],
                    )
                ],
                org, repo, year, month, db_path=db_path,
            )
            seal_month(org, repo, year, month, db_path=db_path)


class TestDashboardWizardRenders:
    def test_should_render_html_and_open_browser(
        self, tmp_path, monkeypatch, _stub_webbrowser
    ):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_feb_mar_apr(db_path)
        monkeypatch.chdir(tmp_path)

        # Act
        dashboard_wizard(db_path=db_path, ask_months=lambda _months: [(2026, 3), (2026, 4)])

        # Assert
        results_dir = tmp_path / "metrics_results"
        matches = list(results_dir.glob("dashboard_*_2026-03-to-2026-04.html"))
        assert matches
        _stub_webbrowser.assert_called_once_with(matches[0].resolve().as_uri())


class TestDashboardWizardEmptyCache:
    def test_should_error_when_no_synced_months(self, tmp_path, capsys):
        # Arrange
        db_path = tmp_path / "cache.db"

        # Act
        with pytest.raises(typer.Exit) as exc:
            dashboard_wizard(db_path=db_path)

        # Assert
        assert exc.value.exit_code == 1
        assert "no synced months" in capsys.readouterr().err.lower()


class TestDashboardWizardCancelled:
    def test_should_exit_when_user_picks_nothing(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_feb_mar_apr(db_path)

        # Act + Assert
        with pytest.raises(typer.Exit) as exc:
            dashboard_wizard(db_path=db_path, ask_months=lambda _months: [])

        assert exc.value.exit_code == 1

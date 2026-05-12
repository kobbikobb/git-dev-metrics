import pytest
import typer

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli.report_wizard import report_wizard

from .conftest import any_pr, approved_review


def _seed_feb_mar_apr(db_path) -> None:
    """One PR per month across Feb–Apr for two repos."""
    for org, repo in (("myorg", "repoA"), ("myorg", "repoB")):
        for year, month, day in ((2026, 2, 5), (2026, 3, 7), (2026, 4, 9)):
            insert_prs(
                [
                    any_pr(
                        number=year * 100 + month,
                        user={"login": "alice"},
                        additions=20,
                        deletions=5,
                        changed_files=2,
                        created_at=f"2026-{month:02d}-{day:02d}T08:00:00Z",
                        merged_at=f"2026-{month:02d}-{day:02d}T16:00:00Z",
                        closed_at=f"2026-{month:02d}-{day:02d}T16:00:00Z",
                        reviews=[approved_review(login="bob")],
                    )
                ],
                org,
                repo,
                year,
                month,
                db_path=db_path,
            )
            seal_month(org, repo, year, month, db_path=db_path)


class TestReportWizardRenders:
    def test_should_offer_union_of_synced_months_and_render_selection(self, tmp_path, monkeypatch):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_feb_mar_apr(db_path)
        monkeypatch.chdir(tmp_path)
        captured: list[list[tuple[int, int]]] = []

        def ask_months(months):
            captured.append(list(months))
            return [(2026, 3), (2026, 4)]

        # Act
        report_wizard(db_path=db_path, ask_months=ask_months)

        # Assert
        assert captured[0] == [(2026, 4), (2026, 3), (2026, 2)]
        results_dir = tmp_path / "metrics_results"
        assert list(results_dir.glob("metrics_*_2026-03-to-2026-04.md"))
        assert list(results_dir.glob("metrics_*_2026-03-to-2026-04.html"))


class TestReportWizardEmptyCache:
    def test_should_error_when_no_synced_months(self, tmp_path, capsys):
        # Arrange
        db_path = tmp_path / "cache.db"

        # Act
        with pytest.raises(typer.Exit) as exc:
            report_wizard(db_path=db_path)

        # Assert
        assert exc.value.exit_code == 1
        assert "no synced months" in capsys.readouterr().err.lower()


class TestReportWizardCancelled:
    def test_should_exit_when_user_picks_nothing(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_feb_mar_apr(db_path)

        # Act + Assert
        with pytest.raises(typer.Exit) as exc:
            report_wizard(db_path=db_path, ask_months=lambda _months: [])

        assert exc.value.exit_code == 1

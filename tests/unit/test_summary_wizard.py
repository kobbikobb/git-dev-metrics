import pytest
import typer

from git_dev_metrics.cache import insert_prs, seal_month
from git_dev_metrics.cli.summary import _summary_wizard as summary_wizard

from .conftest import any_pr, approved_review, dt


def _seed_feb_mar_apr(db_path) -> None:
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
                        created_at=dt(year=year, month=month, day=day, hour=8, minute=0),
                        merged_at=dt(year=year, month=month, day=day, hour=16, minute=0),
                        closed_at=dt(year=year, month=month, day=day, hour=16, minute=0),
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


class TestSummaryWizardRenders:
    def test_should_offer_synced_months_and_print_to_console(self, tmp_path, capsys):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_feb_mar_apr(db_path)
        captured: list[list[tuple[int, int]]] = []

        def ask_months(months):
            captured.append(list(months))
            return [(2026, 3), (2026, 4)]

        # Act
        summary_wizard(db_path=db_path, ask_months=ask_months)

        # Assert
        assert captured[0] == [(2026, 4), (2026, 3), (2026, 2)]
        printed = capsys.readouterr().out
        assert "Summary (2026-03-01 to 2026-05-01)" in printed
        assert "Total PRs" in printed


class TestSummaryWizardEmptyCache:
    def test_should_error_when_no_synced_months(self, tmp_path, capsys):
        # Arrange
        db_path = tmp_path / "cache.db"

        # Act
        with pytest.raises(typer.Exit) as exc:
            summary_wizard(db_path=db_path)

        # Assert
        assert exc.value.exit_code == 1
        assert "no synced months" in capsys.readouterr().err.lower()


class TestSummaryWizardCancelled:
    def test_should_exit_when_user_picks_nothing(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        _seed_feb_mar_apr(db_path)

        # Act + Assert
        with pytest.raises(typer.Exit) as exc:
            summary_wizard(db_path=db_path, ask_months=lambda _months: [])

        assert exc.value.exit_code == 1

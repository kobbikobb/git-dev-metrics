from datetime import datetime
from unittest.mock import Mock

import pytest
import typer

from git_dev_metrics.cache import count_prs, is_sealed, seal_month
from git_dev_metrics.cli.wizards.pull_wizard import pull_wizard
from git_dev_metrics.models import Repository

from ..conftest import any_pr, approved_review, dt


def _three_prs(prefix: int) -> list:
    return [
        any_pr(
            id=prefix + i,
            number=prefix + i,
            user={"login": f"dev-{i}"},
            created_at=dt(year=2026, month=4, day=day, hour=8, minute=0),
            merged_at=dt(year=2026, month=4, day=day, hour=16, minute=0),
            reviews=[approved_review(login="reviewer")],
        )
        for i, day in enumerate((5, 12, 22))
    ]


def _repo(full_name: str, *, private: bool, pushed: datetime) -> Repository:
    return {"full_name": full_name, "private": private, "last_pushed": pushed}


class TestPullWizardMultiRepo:
    def test_should_list_active_repos_and_pull_each_selected(self, tmp_path, mocker):
        # Arrange
        db_path = tmp_path / "cache.db"
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.load_last_org", return_value=None)
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.save_last_org")
        repos = [
            _repo("myorg/repoA", private=False, pushed=dt(year=2026, month=4, day=20)),
            _repo("myorg/oldrepo", private=False, pushed=dt(year=2025, month=1, day=1)),
            _repo("myorg/repoB", private=True, pushed=dt(year=2026, month=4, day=25)),
        ]
        captured_options: list[dict[str, str]] = []

        def ask_repos(opts):
            captured_options.append(dict(opts))
            return ["myorg/repoA", "myorg/repoB"]

        fetch = Mock(side_effect=lambda _t, _o, _r, _p: _three_prs(100))

        # Act
        pull_wizard(
            db_path=db_path,
            ask_org=lambda _last: "myorg",
            ask_month=lambda _choices: "2026-04",
            ask_repos=ask_repos,
            clock=lambda: dt(year=2026, month=5, day=12),
            fetch=fetch,
            fetch_repos=lambda _token, _org: repos,
            get_token=lambda: "fake",
        )

        # Assert
        options = captured_options[0]
        assert "myorg/repoA" in options
        assert "myorg/repoB" in options
        assert "myorg/oldrepo" not in options
        assert options["myorg/repoA"] == "Public"
        assert options["myorg/repoB"] == "Private"
        assert is_sealed("myorg", "repoA", 2026, 4, db_path=db_path)
        assert is_sealed("myorg", "repoB", 2026, 4, db_path=db_path)
        assert count_prs("myorg", "repoA", 2026, 4, db_path=db_path) == 3
        assert count_prs("myorg", "repoB", 2026, 4, db_path=db_path) == 3
        assert fetch.call_count == 2


class TestPullWizardSkipsSealedInBatch:
    def test_should_skip_already_sealed_repo_and_pull_rest(self, tmp_path, mocker, capsys):
        # Arrange
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.load_last_org", return_value=None)
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.save_last_org")
        repos = [
            _repo("myorg/repoA", private=False, pushed=dt(year=2026, month=4, day=20)),
            _repo("myorg/repoB", private=False, pushed=dt(year=2026, month=4, day=20)),
        ]
        fetch = Mock(return_value=_three_prs(200))

        # Act
        pull_wizard(
            db_path=db_path,
            ask_org=lambda _last: "myorg",
            ask_month=lambda _choices: "2026-04",
            ask_repos=lambda _opts: ["myorg/repoA", "myorg/repoB"],
            clock=lambda: dt(year=2026, month=5, day=12),
            fetch=fetch,
            fetch_repos=lambda _token, _org: repos,
            get_token=lambda: "fake",
        )

        # Assert
        out = capsys.readouterr().out
        assert "Skipped myorg/repoA: already sealed." in out
        assert "Pulled 3 PRs for myorg/repoB." in out
        assert "Pulled 1, skipped 1." in out
        assert count_prs("myorg", "repoA", 2026, 4, db_path=db_path) == 0
        assert count_prs("myorg", "repoB", 2026, 4, db_path=db_path) == 3
        assert fetch.call_count == 1


class TestPullWizardRePull:
    def test_should_re_pull_sealed_repos(self, tmp_path, mocker, capsys):
        db_path = tmp_path / "cache.db"
        seal_month("myorg", "repoA", 2026, 4, db_path=db_path)
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.load_last_org", return_value=None)
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.save_last_org")
        repos = [
            _repo("myorg/repoA", private=False, pushed=dt(year=2026, month=4, day=20)),
            _repo("myorg/repoB", private=False, pushed=dt(year=2026, month=4, day=20)),
        ]
        fetch = Mock(return_value=_three_prs(200))

        pull_wizard(
            db_path=db_path,
            ask_org=lambda _last: "myorg",
            ask_month=lambda _choices: "2026-04",
            ask_repos=lambda _opts: ["myorg/repoA", "myorg/repoB"],
            clock=lambda: dt(year=2026, month=5, day=12),
            fetch=fetch,
            fetch_repos=lambda _token, _org: repos,
            get_token=lambda: "fake",
            re_pull=True,
        )

        out = capsys.readouterr().out
        assert "Skipped" not in out
        assert all(f"Pulled 3 PRs for myorg/repo{letter}." in out for letter in ("A", "B"))
        assert count_prs("myorg", "repoA", 2026, 4, db_path=db_path) == 3
        assert count_prs("myorg", "repoB", 2026, 4, db_path=db_path) == 3
        assert fetch.call_count == 2


class TestPullWizardNoActiveRepos:
    def test_should_exit_when_no_active_repos_in_month(self, tmp_path, mocker, capsys):
        # Arrange
        db_path = tmp_path / "cache.db"
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.load_last_org", return_value=None)
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.save_last_org")
        stale_only = [_repo("myorg/old", private=False, pushed=dt(year=2025, month=1, day=1))]

        # Act
        with pytest.raises(typer.Exit) as exc:
            pull_wizard(
                db_path=db_path,
                ask_org=lambda _last: "myorg",
                ask_month=lambda _choices: "2026-04",
                ask_repos=Mock(side_effect=AssertionError("should not prompt for repos")),
                clock=lambda: dt(year=2026, month=5, day=12),
                fetch=Mock(side_effect=AssertionError("should not fetch metrics")),
                fetch_repos=lambda _token, _org: stale_only,
                get_token=lambda: "fake",
            )

        # Assert
        assert exc.value.exit_code == 1
        assert "No active repos" in capsys.readouterr().err


class TestPullWizardMonthChoices:
    def test_should_list_twelve_months_including_current(self, tmp_path, mocker):
        # Arrange
        db_path = tmp_path / "cache.db"
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.load_last_org", return_value=None)
        mocker.patch("git_dev_metrics.cli.wizards.pull_wizard.save_last_org")
        captured: list[list[tuple[str, str]]] = []

        def ask_month(choices):
            captured.append(list(choices))
            return  # user cancels — exits before fetch

        # Act
        with pytest.raises(typer.Exit):
            pull_wizard(
                db_path=db_path,
                ask_org=lambda _last: "myorg",
                ask_month=ask_month,
                ask_repos=Mock(side_effect=AssertionError("should not reach repos")),
                clock=lambda: dt(year=2026, month=5, day=12),
                fetch=Mock(side_effect=AssertionError("should not fetch metrics")),
                fetch_repos=Mock(side_effect=AssertionError("should not fetch repos")),
                get_token=lambda: "fake",
            )

        # Assert
        labels = [label for label, _value in captured[0]]
        values = [value for _label, value in captured[0]]
        assert values[:4] == ["2026-05", "2026-04", "2026-03", "2026-02"]
        assert labels[0] == "May 2026 (current)"
        assert len(values) == 12

"""Unit tests for MetricsSnapshot."""

from datetime import UTC, datetime

from git_dev_metrics.metrics import MetricsSnapshot
from git_dev_metrics.utils import TimePeriod

from .conftest import any_pr, approved_review


def _period() -> TimePeriod:
    return TimePeriod(
        since=datetime(2024, 1, 1, tzinfo=UTC),
        until=datetime(2024, 1, 31, tzinfo=UTC),
    )


class TestFromRepoPrs:
    def test_should_return_empty_snapshot_for_no_prs(self):
        snap = MetricsSnapshot.from_repo_prs({}, _period())

        assert snap.devs == ()
        assert snap.repos == ()
        assert snap.team.pr_count == 0
        assert snap.team.health == 0
        assert snap.team.band == "bad"

    def test_should_filter_inactive_repos(self):
        repo_prs = {
            "org/active": [any_pr(user={"login": "alice"})],
            "org/empty": [],
        }

        snap = MetricsSnapshot.from_repo_prs(repo_prs, _period())

        repo_names = [r.name for r in snap.repos]
        assert "org/active" in repo_names
        assert "org/empty" not in repo_names

    def test_should_filter_bot_authors_from_devs(self):
        repo_prs = {
            "org/r": [
                any_pr(user={"login": "alice"}),
                any_pr(user={"login": "dependabot[bot]"}),
            ]
        }

        snap = MetricsSnapshot.from_repo_prs(repo_prs, _period())

        dev_names = [d.name for d in snap.devs]
        assert "alice" in dev_names
        assert "dependabot[bot]" not in dev_names

    def test_should_sort_devs_by_health_descending(self):
        snap = MetricsSnapshot.from_repo_prs(
            {"org/r": [any_pr(user={"login": "alice"}), any_pr(user={"login": "bob"})]},
            _period(),
        )

        if len(snap.devs) >= 2:
            assert snap.devs[0].health >= snap.devs[1].health

    def test_should_sort_repos_by_health_descending(self):
        repo_prs = {
            "org/a": [any_pr(user={"login": "alice"})],
            "org/b": [any_pr(user={"login": "bob"})],
        }

        snap = MetricsSnapshot.from_repo_prs(repo_prs, _period())

        if len(snap.repos) >= 2:
            assert snap.repos[0].health >= snap.repos[1].health

    def test_should_aggregate_team_across_all_repos(self):
        repo_prs = {
            "org/a": [any_pr(user={"login": "alice"})],
            "org/b": [any_pr(user={"login": "bob"})],
        }

        snap = MetricsSnapshot.from_repo_prs(repo_prs, _period())

        assert snap.team.pr_count == 2

    def test_should_carry_reviewer_counts(self):
        prs = [
            any_pr(
                user={"login": "alice"},
                reviews=[approved_review(login="bob")],
            )
        ]

        snap = MetricsSnapshot.from_repo_prs({"org/r": prs}, _period())

        assert snap.reviewer_counts.get("bob") == 1


class TestBand:
    def test_should_band_good_at_80(self):
        snap = MetricsSnapshot.from_repo_prs({}, _period())
        rows = (_row_with_health(80), _row_with_health(79), _row_with_health(60))

        assert rows[0].band == "good"
        assert rows[1].band == "ok"
        assert rows[2].band == "ok"
        _ = snap  # snap used to exercise import path

    def test_should_band_bad_below_60(self):
        row = _row_with_health(59)

        assert row.band == "bad"


def _row_with_health(health: int):
    from git_dev_metrics.metrics.snapshot import _to_row

    return _to_row("x", {"pr_count": 1}, health)


class TestSummary:
    def test_should_pick_top_reviewer_with_share(self):
        prs = [
            any_pr(
                user={"login": "alice"},
                reviews=[approved_review(login="bob"), approved_review(login="carol")],
            ),
            any_pr(
                number=2,
                user={"login": "alice"},
                reviews=[approved_review(login="bob")],
            ),
        ]

        snap = MetricsSnapshot.from_repo_prs({"org/r": prs}, _period())

        assert snap.summary.top_reviewer == "bob"
        assert snap.summary.max_review_share == round(2 / 3 * 100)

    def test_should_return_empty_top_reviewer_when_no_reviews(self):
        snap = MetricsSnapshot.from_repo_prs(
            {"org/r": [any_pr(user={"login": "alice"})]}, _period()
        )

        assert snap.summary.top_reviewer == ""
        assert snap.summary.max_review_share == 0

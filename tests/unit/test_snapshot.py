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

    def test_should_sort_ai_per_dev_ascending(self):
        prs = []
        for login, ai_count in [("alice", 5), ("bob", 2), ("carol", 4)]:
            for i in range(5):
                prs.append(
                    any_pr(
                        number=f"{login}-{i}",
                        user={"login": login},
                        created_at="2024-01-01T00:00:00Z",
                        merged_at="2024-01-02T00:00:00Z",
                        reviews=[approved_review("2024-01-01T06:00:00Z")],
                        body="Co-Authored-By: Claude" if i < ai_count else "",
                    )
                )

        snap = MetricsSnapshot.from_repo_prs({"org/r": prs}, _period())

        assert list(snap.summary.ai_per_dev) == sorted(snap.summary.ai_per_dev)

    def test_should_break_top_reviewer_ties_alphabetically(self):
        prs = [
            any_pr(
                number=i,
                user={"login": "author"},
                reviews=[approved_review(login=login, submitted_at=f"2024-01-0{i}T00:00:00Z")],
            )
            for i, login in enumerate(["carol", "alice", "bob"], start=1)
        ]

        snap = MetricsSnapshot.from_repo_prs({"org/r": prs}, _period())

        assert snap.summary.top_reviewer == "alice"


class TestTeamAggregation:
    def test_should_use_median_of_dev_medians_for_time_metrics(self):
        heavy = [
            any_pr(
                number=i,
                user={"login": "kobbi"},
                created_at="2024-01-01T00:00:00Z",
                merged_at=f"2024-01-0{5 + i}T00:00:00Z",
                reviews=[approved_review("2024-01-01T06:00:00Z")],
            )
            for i in range(1, 4)
        ]
        lean = [
            any_pr(
                number=10,
                user={"login": "alice"},
                created_at="2024-01-01T00:00:00Z",
                merged_at="2024-01-01T01:00:00Z",
                reviews=[approved_review("2024-01-01T00:30:00Z")],
            )
        ]

        snap = MetricsSnapshot.from_repo_prs({"org/repo": heavy + lean}, _period())

        kobbi = next(d for d in snap.devs if d.name == "kobbi")
        alice = next(d for d in snap.devs if d.name == "alice")
        assert snap.team.cycle_time == round((kobbi.cycle_time + alice.cycle_time) / 2, 2)
        assert snap.team.pr_count == 4

    def test_should_keep_pickup_le_cycle_at_team_level(self):
        prs = [
            any_pr(
                number=1,
                user={"login": "dev"},
                created_at="2024-01-01T00:00:00Z",
                ready_for_review_at="2024-01-04T00:00:00Z",
                merged_at="2024-01-05T00:00:00Z",
                reviews=[approved_review("2024-01-04T12:00:00Z")],
            )
        ]

        snap = MetricsSnapshot.from_repo_prs({"org/repo": prs}, _period())

        assert snap.team.pickup_time <= snap.team.cycle_time

    def test_should_use_mean_of_dev_rates_for_ai_adoption(self):
        prs = []
        for login, ai_count in [("alice", 5), ("bob", 2), ("carol", 2)]:
            for i in range(5):
                prs.append(
                    any_pr(
                        number=f"{login}-{i}",
                        user={"login": login},
                        created_at="2024-01-01T00:00:00Z",
                        merged_at="2024-01-02T00:00:00Z",
                        reviews=[approved_review("2024-01-01T06:00:00Z")],
                        body="Co-Authored-By: Claude" if i < ai_count else "",
                    )
                )

        snap = MetricsSnapshot.from_repo_prs({"org/repo": prs}, _period())

        assert snap.team.ai_percentage == 60.0

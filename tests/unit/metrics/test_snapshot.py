"""Unit tests for MetricsSnapshot."""

from git_dev_metrics.metrics import MetricsSnapshot
from git_dev_metrics.metrics.snapshot import Row, build_summary
from git_dev_metrics.utils import TimePeriod

from ..conftest import any_pr, approved_review, dt


def _period() -> TimePeriod:
    return TimePeriod(
        since=dt(year=2024, month=1, day=1),
        until=dt(year=2024, month=1, day=31),
    )


def _row_with_health(health: int):
    from git_dev_metrics.metrics._health_ranking import raw_to_row as _raw_to_row
    from git_dev_metrics.metrics._raw_metrics import RawMetrics

    return _raw_to_row(
        "x",
        RawMetrics(
            pr_count=1,
            cycle_time=0,
            pickup_time=0,
            review_time=0,
            pr_size=0,
            avg_lines_per_pr=0,
            prs_per_week=0,
            reviews_given=0,
            ai_percentage=0,
        ),
        health,
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
                        created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                        merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                        reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
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
                reviews=[
                    approved_review(
                        login=login, submitted_at=dt(year=2024, month=1, day=i, hour=0, minute=0)
                    )
                ],
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
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=5 + i, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            )
            for i in range(1, 4)
        ]
        lean = [
            any_pr(
                number=10,
                user={"login": "alice"},
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=1, hour=1, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=0, minute=30))],
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
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                ready_for_review_at=dt(year=2024, month=1, day=4, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=5, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=4, hour=12, minute=0))],
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
                        created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                        merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                        reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
                        body="Co-Authored-By: Claude" if i < ai_count else "",
                    )
                )

        snap = MetricsSnapshot.from_repo_prs({"org/repo": prs}, _period())

        assert snap.team.ai_percentage == 60.0


class TestBuildSummary:
    def test_should_build_empty_summary(self) -> None:
        team = Row("team", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "bad")
        summary = build_summary((), {}, team)
        assert summary.top_reviewer == ""
        assert summary.max_review_share == 0
        assert summary.review_ratio == 0.0

    def test_should_pick_top_reviewer(self) -> None:
        devs = (
            Row("alice", 1, 0, 0, 0, 0, 0, 0, 0, 0, 80, "good"),
            Row("bob", 1, 0, 0, 0, 0, 0, 0, 0, 0, 80, "good"),
        )
        team = Row("team", 5, 0, 0, 0, 0, 0, 0, 7, 0, 80, "good")
        summary = build_summary(devs, {"bob": 5, "alice": 2}, team)
        assert summary.top_reviewer == "bob"
        assert summary.max_review_share == round(5 / 7 * 100)
        assert summary.review_ratio == round(7 / 5, 2)

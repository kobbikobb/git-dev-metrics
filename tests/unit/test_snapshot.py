"""Unit tests for MetricsSnapshot."""

from git_dev_metrics.metrics import MetricsSnapshot
from git_dev_metrics.metrics._dev_repo_metrics import compute_metrics_dict
from git_dev_metrics.metrics._health_ranking import band_from_health, dict_to_row, rank_rows
from git_dev_metrics.metrics.snapshot import Row, build_summary
from git_dev_metrics.utils import TimePeriod

from .conftest import any_pr, approved_review, dt


def _period() -> TimePeriod:
    return TimePeriod(
        since=dt(year=2024, month=1, day=1),
        until=dt(year=2024, month=1, day=31),
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
    from git_dev_metrics.metrics._health_ranking import dict_to_row as _dict_to_row

    return _dict_to_row("x", {"pr_count": 1}, health)


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


class TestBandFromHealth:
    def test_should_return_good_above_80(self) -> None:
        assert band_from_health(80) == "good"
        assert band_from_health(95) == "good"

    def test_should_return_ok_between_60_and_79(self) -> None:
        assert band_from_health(60) == "ok"
        assert band_from_health(79) == "ok"

    def test_should_return_bad_below_60(self) -> None:
        assert band_from_health(0) == "bad"
        assert band_from_health(59) == "bad"


class TestDictToRow:
    def test_should_build_row_with_health_and_band(self) -> None:
        row = dict_to_row("alice", {"pr_count": 5, "cycle_time": 12.5}, 85)
        assert row.name == "alice"
        assert row.pr_count == 5
        assert row.cycle_time == 12.5
        assert row.health == 85
        assert row.band == "good"

    def test_should_default_missing_fields(self) -> None:
        row = dict_to_row("bob", {}, 0)
        assert row.pr_count == 0
        assert row.cycle_time == 0.0
        assert row.reviews_given == 0
        assert row.band == "bad"

    def test_should_cast_types(self) -> None:
        row = dict_to_row(
            "carol",
            {
                "pr_count": "3",
                "cycle_time": "10.5",
                "pickup_time": "2.0",
                "review_time": "5.0",
                "pr_size": "50",
                "avg_lines_per_pr": "100.0",
                "prs_per_week": "1.5",
                "reviews_given": "7",
                "ai_percentage": "40.0",
            },
            75,
        )
        assert row.pr_count == 3
        assert row.cycle_time == 10.5
        assert row.pickup_time == 2.0
        assert row.review_time == 5.0
        assert row.pr_size == 50
        assert row.avg_lines_per_pr == 100.0
        assert row.prs_per_week == 1.5
        assert row.reviews_given == 7
        assert row.ai_percentage == 40.0
        assert row.band == "ok"


class TestRankRows:
    def test_should_sort_by_health_descending(self) -> None:
        raws = {"a": {"pr_count": 1}, "b": {"pr_count": 3}, "c": {"pr_count": 2}}
        result = rank_rows(raws, lambda m, _: m["pr_count"] * 10)
        assert [r.name for r in result] == ["b", "c", "a"]
        assert result[0].health == 30
        assert result[2].health == 10

    def test_should_return_empty_tuple_for_empty_raws(self) -> None:
        assert rank_rows({}, lambda m, _: 0) == ()


class TestComputeMetricsDict:
    def test_should_calculate_all_metrics(self) -> None:
        prs = [
            any_pr(
                number=1,
                user={"login": "alice"},
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            )
        ]
        result = compute_metrics_dict(prs, 31, 3)
        assert result["pr_count"] == 1
        assert result["reviews_given"] == 3
        assert result["cycle_time"] > 0


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

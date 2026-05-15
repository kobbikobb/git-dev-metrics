from git_dev_metrics.metrics._health_ranking import (
    band_from_health,
    dict_to_row,
    rank_rows,
)


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

from git_dev_metrics.metrics.trend_calculator import build_trend_dataset
from git_dev_metrics.models import PullRequest

from ..conftest import any_pr, approved_review, dt


def _pr(pr_id: int, login: str, year: int, month: int, day: int) -> PullRequest:
    return any_pr(
        id=pr_id,
        number=pr_id,
        user={"login": login},
        created_at=dt(year=year, month=month, day=day, hour=8, minute=0),
        merged_at=dt(year=year, month=month, day=day, hour=18, minute=0),
        reviews=[
            approved_review(submitted_at=dt(year=year, month=month, day=day, hour=12, minute=0))
        ],
    )


class TestBuildTrendDatasetFiltersLeavers:
    def test_should_only_include_devs_active_in_latest_month(self):
        # Arrange
        feb = [
            _pr(1, "alice", 2026, 2, 5),
            _pr(2, "alice", 2026, 2, 12),
            _pr(3, "bob", 2026, 2, 7),
            _pr(4, "charlie", 2026, 2, 9),
            _pr(5, "charlie", 2026, 2, 11),
            _pr(6, "charlie", 2026, 2, 19),
        ]
        mar = [_pr(7, "alice", 2026, 3, 4), _pr(8, "bob", 2026, 3, 10), _pr(9, "bob", 2026, 3, 21)]
        apr = [
            _pr(10, "alice", 2026, 4, 3),
            _pr(11, "alice", 2026, 4, 11),
            _pr(12, "alice", 2026, 4, 22),
            _pr(13, "bob", 2026, 4, 8),
            _pr(14, "bob", 2026, 4, 18),
        ]
        months = [(2026, 2), (2026, 3), (2026, 4)]
        prs_per_month: dict[tuple[int, int], list[PullRequest]] = {
            (2026, 2): feb,
            (2026, 3): mar,
            (2026, 4): apr,
        }

        # Act
        dataset = build_trend_dataset(months, prs_per_month)

        # Assert
        assert dataset.devs == ["alice", "bob"]
        assert dataset.months == ["2026-02", "2026-03", "2026-04"]
        assert dataset.rows["alice"][0].pr_count == 2
        assert dataset.rows["alice"][2].pr_count == 3
        assert dataset.rows["bob"][0].pr_count == 1
        assert dataset.rows["bob"][2].pr_count == 2


class TestBuildTrendDatasetEmpty:
    def test_should_return_empty_dataset_when_no_months(self):
        # Arrange
        months: list[tuple[int, int]] = []
        prs_per_month: dict[tuple[int, int], list] = {}

        # Act
        dataset = build_trend_dataset(months, prs_per_month)

        # Assert
        assert dataset.months == []
        assert dataset.devs == []
        assert dataset.rows == {}

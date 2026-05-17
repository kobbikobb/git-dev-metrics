from git_dev_metrics.metrics._dev_repo_metrics import compute_raw

from ..conftest import any_pr, approved_review, dt


class TestComputeRaw:
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
        result = compute_raw(prs, 31, 3)
        assert result.pr_count == 1
        assert result.reviews_given == 3
        assert result.cycle_time > 0

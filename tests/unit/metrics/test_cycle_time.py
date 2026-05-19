from git_dev_metrics.metrics import calculate_cycle_time

from ..conftest import any_pr, approved_review, dt


class TestCalculateCycleTime:
    def test_should_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_cycle_time(prs)
        assert result == 0.0

    def test_should_return_correct_cycle_time_for_single_pr(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            )
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_return_average_cycle_time_for_multiple_prs(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            ),
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 36.0

    def test_should_handle_prs_with_different_time_zones(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=12, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=12, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=18, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_use_first_commit_when_older_than_created_at(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                first_commit_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=2, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_use_created_at_when_older_than_first_commit(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                first_commit_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=2, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_use_created_at_when_first_commit_is_none(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                first_commit_at=None,
                reviews=[approved_review(dt(year=2024, month=1, day=1, hour=6, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_exclude_draft_window_using_ready_for_review_at(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                ready_for_review_at=dt(year=2024, month=1, day=4, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=5, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=4, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 24.0

    def test_should_ignore_ready_for_review_when_before_start_time(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                first_commit_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                ready_for_review_at=dt(year=2023, month=12, day=31, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=2, hour=12, minute=0))],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 48.0

    def test_should_skip_prs_without_approval(self):
        prs = [
            any_pr(
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[],
            ),
        ]

        result = calculate_cycle_time(prs)

        assert result == 0.0

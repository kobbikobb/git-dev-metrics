from git_dev_metrics.metrics import calculate_pickup_time, calculate_review_time

from ..conftest import any_pr, approved_review, dt


class TestCalculatePickupTime:
    def test_should_return_zero_when_no_prs_provided(self):
        result = calculate_pickup_time([])
        assert result == 0.0

    def test_should_return_zero_when_no_reviews(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "COMMENTED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=12, minute=0),
                    }
                ],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 0.0

    def test_should_calculate_pickup_time(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "APPROVED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=12, minute=0),
                    }
                ],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 12.0

    def test_should_exclude_draft_window_from_pickup(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                ready_for_review_at=dt(year=2024, month=1, day=4, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=5, hour=0, minute=0),
                reviews=[approved_review(dt(year=2024, month=1, day=4, hour=6, minute=0))],
            )
        ]
        result = calculate_pickup_time(prs)
        assert result == 6.0


class TestCalculateReviewTime:
    def test_should_return_zero_when_no_prs_provided(self):
        result = calculate_review_time([])
        assert result == 0.0

    def test_should_return_zero_when_no_approval(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=2, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "COMMENTED",
                        "submitted_at": dt(year=2024, month=1, day=1, hour=12, minute=0),
                    }
                ],
            )
        ]
        result = calculate_review_time(prs)
        assert result == 0.0

    def test_should_calculate_review_time(self):
        prs = [
            any_pr(
                number=1,
                created_at=dt(year=2024, month=1, day=1, hour=0, minute=0),
                merged_at=dt(year=2024, month=1, day=3, hour=0, minute=0),
                reviews=[
                    {
                        "user": {"login": "reviewer"},
                        "state": "APPROVED",
                        "submitted_at": dt(year=2024, month=1, day=2, hour=0, minute=0),
                    }
                ],
            )
        ]
        result = calculate_review_time(prs)
        assert result == 24.0

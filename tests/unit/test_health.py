import pytest

from git_dev_metrics.metrics.health import calculate_health_score, calc_benchmark_penalty


class TestCalcBenchmarkPenalty:
    """Test cases for calc_benchmark_penalty function."""

    def test_should_return_zero_for_unknown_metric(self):
        result = calc_benchmark_penalty(10, "unknown")
        assert result == 0

    def test_should_return_zero_for_zero_value(self):
        result = calc_benchmark_penalty(0, "cycle_time")
        assert result == 0

    def test_should_return_zero_for_negative_value(self):
        result = calc_benchmark_penalty(-1, "cycle_time")
        assert result == 0

    def test_should_return_zero_for_excellent_cycle_time(self):
        result = calc_benchmark_penalty(2, "cycle_time")
        assert result == 0

    def test_should_return_zero_for_good_cycle_time(self):
        result = calc_benchmark_penalty(20, "cycle_time")
        assert result == 0

    def test_should_return_20_for_ok_cycle_time(self):
        result = calc_benchmark_penalty(50, "cycle_time")
        assert result == 20

    def test_should_return_35_for_bad_cycle_time(self):
        result = calc_benchmark_penalty(100, "cycle_time")
        assert result == 35

    def test_should_return_zero_for_excellent_pr_size(self):
        result = calc_benchmark_penalty(50, "pr_size")
        assert result == 0

    def test_should_return_zero_for_good_pr_size(self):
        result = calc_benchmark_penalty(200, "pr_size")
        assert result == 0

    def test_should_return_20_for_ok_pr_size(self):
        result = calc_benchmark_penalty(600, "pr_size")
        assert result == 20

    def test_should_return_20_for_bad_pr_size(self):
        result = calc_benchmark_penalty(1000, "pr_size")
        assert result == 20

    def test_should_return_zero_for_excellent_prs_per_week(self):
        result = calc_benchmark_penalty(6, "prs_per_week")
        assert result == 0

    def test_should_return_zero_for_good_prs_per_week(self):
        result = calc_benchmark_penalty(4, "prs_per_week")
        assert result == 0

    def test_should_return_20_for_ok_prs_per_week(self):
        result = calc_benchmark_penalty(2, "prs_per_week")
        assert result == 20

    def test_should_return_30_for_bad_prs_per_week(self):
        result = calc_benchmark_penalty(1, "prs_per_week")
        assert result == 30


class TestCalculateHealthScore:
    """Test cases for calculate_health_score function."""

    def test_should_return_100_for_perfect_metrics(self):
        metrics = {
            "cycle_time": 2,
            "pr_size": 50,
            "prs_per_week": 6,
            "pr_count": 5,
            "reviews_given": 5,
        }
        result = calculate_health_score(metrics)
        assert result == 100

    def test_should_penalize_high_cycle_time(self):
        metrics = {
            "cycle_time": 100,
            "pr_size": 50,
            "prs_per_week": 6,
            "pr_count": 5,
            "reviews_given": 5,
        }
        result = calculate_health_score(metrics)
        assert result == 70

    def test_should_penalize_large_pr_size(self):
        metrics = {
            "cycle_time": 2,
            "pr_size": 1000,
            "prs_per_week": 6,
            "pr_count": 5,
            "reviews_given": 5,
        }
        result = calculate_health_score(metrics)
        assert result == 85

    def test_should_penalize_low_prs_per_week(self):
        metrics = {
            "cycle_time": 2,
            "pr_size": 50,
            "prs_per_week": 1,
            "pr_count": 1,
            "reviews_given": 1,
        }
        result = calculate_health_score(metrics)
        assert result == 75

    def test_should_penalize_low_review_ratio(self):
        metrics = {
            "cycle_time": 2,
            "pr_size": 50,
            "prs_per_week": 6,
            "pr_count": 10,
            "reviews_given": 1,
        }
        result = calculate_health_score(metrics)
        assert result == 85

    def test_should_not_penalize_high_review_ratio(self):
        metrics = {
            "cycle_time": 2,
            "pr_size": 50,
            "prs_per_week": 6,
            "pr_count": 5,
            "reviews_given": 10,
        }
        result = calculate_health_score(metrics)
        assert result == 100

    def test_should_return_0_for_worst_metrics(self):
        metrics = {
            "cycle_time": 200,
            "pr_size": 2000,
            "prs_per_week": 0.1,
            "pr_count": 1,
            "reviews_given": 0,
        }
        result = calculate_health_score(metrics)
        assert result == 0

    def test_should_handle_missing_metrics(self):
        metrics = {}
        result = calculate_health_score(metrics)
        assert result == 0

    def test_should_handle_zero_pr_count_no_review_penalty(self):
        metrics = {
            "cycle_time": 2,
            "pr_size": 50,
            "prs_per_week": 6,
            "pr_count": 0,
            "reviews_given": 0,
        }
        result = calculate_health_score(metrics)
        assert result == 0

    def test_should_add_relative_bonus_for_highest_prs_per_week(self):
        all_metrics = [
            {"prs_per_week": 2, "reviews_given": 5, "cycle_time": 10, "pr_count": 2},
            {"prs_per_week": 6, "reviews_given": 3, "cycle_time": 20, "pr_count": 6},
        ]
        metrics = {"prs_per_week": 6, "reviews_given": 3, "cycle_time": 20, "pr_count": 6}
        result = calculate_health_score(metrics, all_metrics)
        assert result == 100

    def test_should_add_relative_bonus_for_most_reviews(self):
        all_metrics = [
            {"prs_per_week": 5, "reviews_given": 2, "cycle_time": 10},
            {"prs_per_week": 3, "reviews_given": 10, "cycle_time": 20},
        ]
        metrics = {"prs_per_week": 3, "reviews_given": 10, "cycle_time": 20, "pr_count": 5}
        result = calculate_health_score(metrics, all_metrics)
        assert result == 100

    def test_should_add_relative_bonus_for_fastest_cycle_time(self):
        all_metrics = [
            {"prs_per_week": 5, "reviews_given": 5, "cycle_time": 10, "pr_count": 5},
            {"prs_per_week": 3, "reviews_given": 3, "cycle_time": 5, "pr_count": 3},
        ]
        metrics = {"prs_per_week": 3, "reviews_given": 3, "cycle_time": 5, "pr_count": 3}
        result = calculate_health_score(metrics, all_metrics)
        assert result == 100

from git_dev_metrics.metrics._rows import RawMetrics
from git_dev_metrics.metrics.health import (
    _citizenship_score,
    _throughput_score,
    _time_score,
    calculate_dev_health_score,
    calculate_health_score,
)


def _raw(**overrides: float | int) -> RawMetrics:
    return RawMetrics(
        pr_count=int(overrides.get("pr_count", 0)),
        prs_per_week=float(overrides.get("prs_per_week", 0)),
        cycle_time=float(overrides.get("cycle_time", 0)),
        pickup_time=float(overrides.get("pickup_time", 0)),
        reviews_given=int(overrides.get("reviews_given", 0)),
        review_time=float(overrides.get("review_time", 0)),
        pr_size=float(overrides.get("pr_size", 0)),
        avg_lines_per_pr=float(overrides.get("avg_lines_per_pr", 0)),
        ai_percentage=float(overrides.get("ai_percentage", 0)),
    )


class TestThroughputScore:
    def test_should_return_zero_for_zero(self):
        assert _throughput_score(0) == 0

    def test_should_return_zero_for_negative(self):
        assert _throughput_score(-1) == 0

    def test_should_return_80_at_good_target(self):
        assert _throughput_score(6) == 80

    def test_should_return_100_at_elite(self):
        assert _throughput_score(60) == 100

    def test_should_cap_at_100_above_elite(self):
        assert _throughput_score(120) == 100

    def test_should_scale_below_good_target(self):
        assert _throughput_score(3) == 40

    def test_should_reward_extreme_volume_above_baseline(self):
        assert _throughput_score(12) > _throughput_score(6)


class TestTimeScore:
    bands = (4, 24, 48, 96)

    def test_should_return_100_for_excellent(self):
        assert _time_score(2, self.bands) == 100

    def test_should_return_80_for_good(self):
        assert _time_score(20, self.bands) == 80

    def test_should_return_60_for_ok(self):
        assert _time_score(40, self.bands) == 60

    def test_should_return_40_for_bad(self):
        assert _time_score(80, self.bands) == 40

    def test_should_return_20_for_very_bad(self):
        assert _time_score(200, self.bands) == 20

    def test_should_treat_zero_as_no_signal(self):
        assert _time_score(0, self.bands) == 100

    def test_should_treat_negative_as_no_signal(self):
        assert _time_score(-50, self.bands) == 100


class TestCitizenshipScore:
    def test_should_return_zero_when_no_prs(self):
        assert _citizenship_score(5, 0) == 0

    def test_should_return_zero_for_zero_reviews(self):
        assert _citizenship_score(0, 5) == 0

    def test_should_score_full_at_2x_ratio_and_full_absolute(self):
        assert _citizenship_score(50, 25) == 75

    def test_should_score_top_absolute_when_team_provided(self):
        all_m = [_raw(reviews_given=300), _raw(reviews_given=50)]
        assert _citizenship_score(300, 100, all_m) == 100

    def test_should_punish_high_volume_author_with_low_relative_reviews(self):
        all_m = [_raw(reviews_given=1000), _raw(reviews_given=100)]
        assert _citizenship_score(100, 200, all_m) == 17.5

    def test_should_reward_prolific_reviewer_at_top_of_team(self):
        all_m = [_raw(reviews_given=335), _raw(reviews_given=35)]
        result = _citizenship_score(335, 264, all_m)
        assert 80 < result < 83


class TestCalculateHealthScore:
    def test_should_return_zero_when_no_prs(self):
        assert calculate_health_score(_raw(pr_count=0)) == 0

    def test_should_return_100_for_elite_metrics(self):
        result = calculate_health_score(
            _raw(pr_count=30, prs_per_week=60, cycle_time=2, pickup_time=1, reviews_given=200)
        )
        assert result == 100

    def test_should_ignore_pr_size(self):
        small = _raw(
            pr_count=30, prs_per_week=60, cycle_time=2, pickup_time=1, reviews_given=200, pr_size=50
        )
        huge = _raw(
            pr_count=30,
            prs_per_week=60,
            cycle_time=2,
            pickup_time=1,
            reviews_given=200,
            pr_size=10000,
            avg_lines_per_pr=5000,
        )
        assert calculate_health_score(small) == calculate_health_score(huge)

    def test_should_penalize_slow_cycle_time(self):
        result = calculate_health_score(
            _raw(pr_count=30, prs_per_week=60, cycle_time=200, pickup_time=1, reviews_given=200)
        )
        assert result == 84

    def test_should_penalize_slow_pickup(self):
        result = calculate_health_score(
            _raw(pr_count=30, prs_per_week=60, cycle_time=2, pickup_time=100, reviews_given=200)
        )
        assert result == 84

    def test_should_penalize_low_throughput(self):
        result = calculate_health_score(
            _raw(pr_count=1, prs_per_week=1, cycle_time=2, pickup_time=1, reviews_given=100)
        )
        assert result == 78

    def test_should_penalize_low_citizenship(self):
        result = calculate_health_score(
            _raw(pr_count=10, prs_per_week=60, cycle_time=2, pickup_time=1, reviews_given=0)
        )
        assert result == 65

    def test_should_handle_negative_pickup_time_as_no_signal(self):
        result = calculate_health_score(
            _raw(pr_count=30, prs_per_week=60, cycle_time=2, pickup_time=-440, reviews_given=200)
        )
        assert result == 100

    def test_should_floor_at_zero(self):
        result = calculate_health_score(
            _raw(pr_count=1, prs_per_week=0, cycle_time=200, pickup_time=100, reviews_given=0)
        )
        assert result == 8

    def test_should_handle_missing_metrics(self):
        assert calculate_health_score(_raw(pr_count=0)) == 0

    def test_should_use_team_max_for_relative_citizenship(self):
        prolific = _raw(
            pr_count=264, prs_per_week=60, cycle_time=2, pickup_time=3, reviews_given=335
        )
        small = _raw(pr_count=23, prs_per_week=5, cycle_time=2, pickup_time=1, reviews_given=35)
        all_m = [prolific, small]

        prolific_score = calculate_health_score(prolific, all_m)
        small_score = calculate_health_score(small, all_m)
        assert prolific_score > small_score


class TestCalculateDevHealthScore:
    def test_should_return_zero_when_no_prs(self):
        assert calculate_dev_health_score(_raw(pr_count=0)) == 0

    def test_should_ignore_pickup_time(self):
        fast_pickup = _raw(
            pr_count=30, prs_per_week=60, cycle_time=2, pickup_time=1, reviews_given=200
        )
        slow_pickup = _raw(
            pr_count=30, prs_per_week=60, cycle_time=2, pickup_time=100, reviews_given=200
        )
        assert calculate_dev_health_score(fast_pickup) == calculate_dev_health_score(slow_pickup)

    def test_should_return_100_for_elite_metrics(self):
        result = calculate_dev_health_score(
            _raw(pr_count=30, prs_per_week=60, cycle_time=2, reviews_given=200)
        )
        assert result == 100

    def test_should_weight_cycle_more_than_team_score(self):
        slow = _raw(pr_count=30, prs_per_week=60, cycle_time=200, pickup_time=1, reviews_given=200)
        assert calculate_dev_health_score(slow) == 76

    def test_should_weight_citizenship_at_45_percent(self):
        assert (
            calculate_dev_health_score(
                _raw(pr_count=10, prs_per_week=60, cycle_time=2, reviews_given=0)
            )
            == 55
        )

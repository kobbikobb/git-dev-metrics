from git_dev_metrics.metrics.health import (
    _citizenship_score,
    _throughput_score,
    _time_score,
    calculate_dev_health_score,
    calculate_health_score,
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
        # 12/wk should clearly beat 6/wk (was tied at 100 in old formula)
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
        # Standalone (no team): 50 absolute (50/100) + 50 ratio (2x) → 75
        assert _citizenship_score(50, 25) == 75

    def test_should_score_top_absolute_when_team_provided(self):
        # Top reviewer in team gets full absolute, even with low ratio
        all_m = [{"reviews_given": 300}, {"reviews_given": 50}]
        # ratio 300/100 = 3 → 100 ratio_score; absolute 300/300 → 100. Avg 100.
        assert _citizenship_score(300, 100, all_m) == 100

    def test_should_punish_high_volume_author_with_low_relative_reviews(self):
        # Big author, modest reviews vs team max
        all_m = [{"reviews_given": 1000}, {"reviews_given": 100}]
        # ratio 100/200 = 0.5 → 25; absolute 100/1000 = 10. Avg 17.5
        assert _citizenship_score(100, 200, all_m) == 17.5

    def test_should_reward_prolific_reviewer_at_top_of_team(self):
        # Kobbi-like: high author volume + top absolute reviews
        all_m = [{"reviews_given": 335}, {"reviews_given": 35}]
        # ratio 335/264 = 1.27 → 63.4; absolute 335/335 → 100. Avg ~81.7
        result = _citizenship_score(335, 264, all_m)
        assert 80 < result < 83


class TestCalculateHealthScore:
    def test_should_return_zero_when_no_prs(self):
        result = calculate_health_score({"pr_count": 0})
        assert result == 0

    def test_should_return_100_for_elite_metrics(self):
        # Arrange: elite throughput + excellent times + top reviewer
        metrics = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 2,
            "pickup_time": 1,
            "reviews_given": 200,
        }

        # Act
        result = calculate_health_score(metrics)

        # Assert
        assert result == 100

    def test_should_ignore_pr_size(self):
        # Arrange: same metrics with vastly different pr_size should score identically
        small = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 2,
            "pickup_time": 1,
            "reviews_given": 200,
            "pr_size": 50,
        }
        huge = {**small, "pr_size": 10000, "avg_lines_per_pr": 5000}

        # Act / Assert
        assert calculate_health_score(small) == calculate_health_score(huge)

    def test_should_penalize_slow_cycle_time(self):
        # Arrange
        metrics = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 200,
            "pickup_time": 1,
            "reviews_given": 200,
        }

        # Act
        result = calculate_health_score(metrics)

        # Assert: speed drops 100→20, costs 0.20*80 = 16 points. 100-16 = 84
        assert result == 84

    def test_should_penalize_slow_pickup(self):
        # Arrange
        metrics = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 2,
            "pickup_time": 100,
            "reviews_given": 200,
        }

        # Act
        result = calculate_health_score(metrics)

        # Assert
        assert result == 84

    def test_should_penalize_low_throughput(self):
        # Arrange
        metrics = {
            "pr_count": 1,
            "prs_per_week": 1,
            "cycle_time": 2,
            "pickup_time": 1,
            "reviews_given": 100,
        }

        # Act
        result = calculate_health_score(metrics)

        # Assert: throughput 13.3 (1/6*80), citizenship 100 (top abs + top ratio).
        # 0.25*13.3 + 0.20*100 + 0.20*100 + 0.35*100 = 78.33 → 78
        assert result == 78

    def test_should_penalize_low_citizenship(self):
        # Arrange
        metrics = {
            "pr_count": 10,
            "prs_per_week": 60,
            "cycle_time": 2,
            "pickup_time": 1,
            "reviews_given": 0,
        }

        # Act
        result = calculate_health_score(metrics)

        # Assert: citizenship 0 (no reviews). 0.25*100 + 0.20*100 + 0.20*100 + 0.35*0 = 65
        assert result == 65

    def test_should_handle_negative_pickup_time_as_no_signal(self):
        # Arrange
        metrics = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 2,
            "pickup_time": -440,
            "reviews_given": 200,
        }

        # Act
        result = calculate_health_score(metrics)

        # Assert
        assert result == 100

    def test_should_floor_at_zero(self):
        # Arrange
        metrics = {
            "pr_count": 1,
            "prs_per_week": 0,
            "cycle_time": 200,
            "pickup_time": 100,
            "reviews_given": 0,
        }

        # Act
        result = calculate_health_score(metrics)

        # Assert: all components 0/20/20/0. 0.25*0 + 0.20*20 + 0.20*20 + 0.35*0 = 8
        assert result == 8

    def test_should_handle_missing_metrics(self):
        result = calculate_health_score({})
        assert result == 0

    def test_should_use_team_max_for_relative_citizenship(self):
        # Arrange: top reviewer in team gets max citizenship even with modest ratio
        prolific = {
            "pr_count": 264,
            "prs_per_week": 60,
            "cycle_time": 2,
            "pickup_time": 3,
            "reviews_given": 335,
        }
        small = {
            "pr_count": 23,
            "prs_per_week": 5,
            "cycle_time": 2,
            "pickup_time": 1,
            "reviews_given": 35,
        }
        all_m = [prolific, small]

        # Act
        prolific_score = calculate_health_score(prolific, all_m)
        small_score = calculate_health_score(small, all_m)

        # Assert: prolific (top reviewer + top throughput) should beat small dev
        assert prolific_score > small_score


class TestCalculateDevHealthScore:
    def test_should_return_zero_when_no_prs(self):
        assert calculate_dev_health_score({"pr_count": 0}) == 0

    def test_should_ignore_pickup_time(self):
        # Arrange: same metrics with vastly different pickup should score identically
        fast_pickup = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 2,
            "pickup_time": 1,
            "reviews_given": 200,
        }
        slow_pickup = {**fast_pickup, "pickup_time": 100}

        # Act / Assert
        assert calculate_dev_health_score(fast_pickup) == calculate_dev_health_score(slow_pickup)

    def test_should_return_100_for_elite_metrics(self):
        # Arrange: elite throughput + excellent cycle + top reviewer
        metrics = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 2,
            "reviews_given": 200,
        }

        # Act
        result = calculate_dev_health_score(metrics)

        # Assert
        assert result == 100

    def test_should_weight_cycle_more_than_team_score(self):
        # Same slow-cycle metrics; dev formula penalizes cycle harder (30% vs 20%)
        slow = {
            "pr_count": 30,
            "prs_per_week": 60,
            "cycle_time": 200,
            "pickup_time": 1,
            "reviews_given": 200,
        }
        # dev score: throughput 100, speed 20, citizenship 100. 0.25*100+0.30*20+0.45*100 = 76
        assert calculate_dev_health_score(slow) == 76

    def test_should_weight_citizenship_at_45_percent(self):
        # No reviews → citizenship 0; everything else 100. 0.25*100 + 0.30*100 + 0.45*0 = 55
        metrics = {
            "pr_count": 10,
            "prs_per_week": 60,
            "cycle_time": 2,
            "reviews_given": 0,
        }
        assert calculate_dev_health_score(metrics) == 55

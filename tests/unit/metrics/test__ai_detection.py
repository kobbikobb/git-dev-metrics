"""Tests for AI co-author detection."""

from ..conftest import any_pr


class TestIsAiCoauthored:
    def test_should_return_false_for_none_body(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body=None))
        assert result is False

    def test_should_return_false_for_empty_body(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body=""))
        assert result is False

    def test_should_return_false_for_no_trailer(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body="This is a regular PR description"))
        assert result is False

    def test_should_return_true_for_coauthored_by_in_body(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body="Co-Authored-By: GitHub <noreply@github.com>"))
        assert result is True

    def test_should_be_case_insensitive(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        result = is_ai_coauthored(any_pr(body="co-authored-by: someone@example.com"))
        assert result is True

    def test_should_return_true_when_trailer_only_in_commit_message(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        pr = any_pr(
            body=None,
            commit_messages=["Fix bug\n\nCo-Authored-By: Claude <noreply@anthropic.com>"],
        )
        result = is_ai_coauthored(pr)
        assert result is True

    def test_should_return_true_when_trailer_in_one_of_many_commits(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        pr = any_pr(
            body="Regular PR",
            commit_messages=[
                "Refactor module",
                "Add tests",
                "Polish\n\n🤖 Generated with Claude Code",
            ],
        )
        result = is_ai_coauthored(pr)
        assert result is True

    def test_should_return_false_when_no_trailer_in_body_or_commits(self):
        from git_dev_metrics.metrics._ai_detection import is_ai_coauthored

        pr = any_pr(
            body="Regular PR",
            commit_messages=["Refactor module", "Add tests"],
        )
        result = is_ai_coauthored(pr)
        assert result is False


class TestCalculateAiPercentage:
    def test_should_return_zero_for_empty_list(self):
        from git_dev_metrics.metrics._ai_detection import calculate_ai_percentage

        result = calculate_ai_percentage([])
        assert result == 0.0

    def test_should_return_zero_for_no_ai_prs(self):
        from git_dev_metrics.metrics._ai_detection import calculate_ai_percentage

        prs = [
            any_pr(body=None),
            any_pr(body="Regular PR"),
            any_pr(body=None),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 0.0

    def test_should_calculate_percentage_correctly(self):
        from git_dev_metrics.metrics._ai_detection import calculate_ai_percentage

        prs = [
            any_pr(body="Co-Authored-By: someone@example.com"),
            any_pr(body="Regular PR"),
            any_pr(body="Co-Authored-By: another@example.com"),
            any_pr(body="Another regular PR"),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 50.0

    def test_should_handle_all_ai_prs(self):
        from git_dev_metrics.metrics._ai_detection import calculate_ai_percentage

        prs = [
            any_pr(body="Co-Authored-By: someone@example.com"),
            any_pr(body="Co-Authored-By: another@example.com"),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 100.0

    def test_should_round_to_one_decimal(self):
        from git_dev_metrics.metrics._ai_detection import calculate_ai_percentage

        prs = [
            any_pr(body="Co-Authored-By: someone@example.com"),
            any_pr(body="Regular PR"),
            any_pr(body="Regular PR"),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 33.3

    def test_should_count_pr_with_trailer_only_in_commit_message(self):
        from git_dev_metrics.metrics._ai_detection import calculate_ai_percentage

        prs = [
            any_pr(body="Regular PR", commit_messages=["Co-Authored-By: Claude"]),
            any_pr(body="Regular PR", commit_messages=["Refactor"]),
        ]
        result = calculate_ai_percentage(prs)
        assert result == 50.0

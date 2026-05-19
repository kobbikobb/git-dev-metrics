from git_dev_metrics.constants import is_bot_login
from git_dev_metrics.metrics.calculator import group_prs_by_devs

from ..conftest import any_pr


class TestIsBotLogin:
    def test_should_match_known_bot(self):
        assert is_bot_login("dependabot") is True

    def test_should_match_dash_bot_suffix(self):
        assert is_bot_login("patches-bot") is True

    def test_should_match_bracket_bot_suffix(self):
        assert is_bot_login("custom[bot]") is True

    def test_should_not_match_human_login(self):
        assert is_bot_login("alice") is False

    def test_should_handle_none(self):
        assert is_bot_login(None) is False


class TestGroupPrsByDevsBotExclusion:
    def test_should_exclude_dash_bot_authors(self):
        prs = [
            any_pr(id=1, number=1, user={"login": "alice"}),
            any_pr(id=2, number=2, user={"login": "patches-bot"}),
        ]
        result = group_prs_by_devs(prs)
        assert "alice" in result
        assert "patches-bot" not in result

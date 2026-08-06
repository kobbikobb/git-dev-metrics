"""Tests for Dependabot alerts REST client."""

import re

import pytest
import responses

from git_dev_metrics.github import (
    GitHubAuthError,
    GitHubNotFoundError,
    fetch_open_pr_security,
)


def _alert(pr_number: int, severity: str, ghsa: str = "GHSA-0001") -> dict:
    return {
        "number": 1,
        "state": "open",
        "dependabot_update": {"pull_request_number": pr_number},
        "security_advisory": {"severity": severity, "ghsa_id": ghsa},
    }


class TestFetchOpenPrSecurity:
    @responses.activate
    def test_should_map_open_alerts_by_pr_number(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo/dependabot/alerts"),
            json=[_alert(42, "critical"), _alert(7, "high", "GHSA-9999")],
            status=200,
        )

        result = fetch_open_pr_security("fake-token", "myorg", "myrepo")

        assert result == {
            42: {"severity": "critical", "advisory_id": "GHSA-0001"},
            7: {"severity": "high", "advisory_id": "GHSA-9999"},
        }

    @responses.activate
    def test_should_skip_alerts_without_pr_link(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo/dependabot/alerts"),
            json=[
                {
                    "number": 1,
                    "state": "open",
                    "dependabot_update": None,
                    "security_advisory": {"severity": "high", "ghsa_id": "GHSA-0001"},
                },
                {
                    "number": 2,
                    "state": "open",
                    "dependabot_update": {"pull_request_number": None},
                    "security_advisory": {"severity": "low", "ghsa_id": "GHSA-0002"},
                },
            ],
            status=200,
        )

        result = fetch_open_pr_security("fake-token", "myorg", "myrepo")

        assert result == {}

    @responses.activate
    def test_should_follow_pagination(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo/dependabot/alerts"),
            json=[_alert(1, "high")],
            status=200,
            headers={
                "Link": (
                    "<https://api.github.com/repos/myorg/myrepo/dependabot/alerts?per_page=100&page=2>"
                    '; rel="next", <https://api.github.com/repos/myorg/myrepo/dependabot/alerts?per_page=100&page=3>'
                    '; rel="last"'
                )
            },
        )
        responses.add(
            responses.GET,
            re.compile(r".*page=2.*"),
            json=[_alert(2, "critical")],
            status=200,
            match_querystring=False,
        )

        result = fetch_open_pr_security("fake-token", "myorg", "myrepo")

        assert set(result) == {1, 2}
        assert result[2] == {"severity": "critical", "advisory_id": "GHSA-0001"}

    @responses.activate
    def test_should_raise_auth_error_on_403(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo/dependabot/alerts"),
            status=403,
        )

        with pytest.raises(GitHubAuthError, match="cannot read security alerts"):
            fetch_open_pr_security("fake-token", "myorg", "myrepo")

    @responses.activate
    def test_should_raise_not_found_on_404(self):
        responses.add(
            responses.GET,
            re.compile(r"https://api\.github\.com/repos/myorg/myrepo/dependabot/alerts"),
            status=404,
        )

        with pytest.raises(GitHubNotFoundError):
            fetch_open_pr_security("fake-token", "myorg", "myrepo")

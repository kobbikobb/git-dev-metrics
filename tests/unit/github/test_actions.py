"""Tests for GitHub Actions workflow-runs REST client."""

import re

import pytest
import responses

from git_dev_metrics.github import (
    GitHubAuthError,
    GitHubNotFoundError,
    fetch_open_pr_build_state,
)

URL = r"https://api\.github\.com/repos/myorg/myrepo/actions/runs"


def _run(status: str, conclusion: str | None) -> dict:
    return {"status": status, "conclusion": conclusion, "head_sha": "abc123"}


class TestFetchOpenPrBuildState:
    @responses.activate
    def test_should_map_runs_by_pr_number(self):
        responses.add(
            responses.GET,
            re.compile(URL),
            json={"workflow_runs": [_run("completed", "success"), _run("completed", "failure")]},
            status=200,
        )

        result = fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: "abc123"})

        assert result == {1: "FAILURE"}

    @responses.activate
    def test_should_report_pending_while_runs_in_progress(self):
        responses.add(
            responses.GET,
            re.compile(URL),
            json={"workflow_runs": [_run("in_progress", None)]},
            status=200,
        )

        result = fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: "abc123"})

        assert result == {1: "PENDING"}

    @responses.activate
    def test_should_report_success_only_when_all_runs_succeed(self):
        responses.add(
            responses.GET,
            re.compile(URL),
            json={"workflow_runs": [_run("completed", "success")]},
            status=200,
        )

        result = fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: "abc123"})

        assert result == {1: "SUCCESS"}

    @responses.activate
    def test_should_omit_pr_without_runs(self):
        responses.add(
            responses.GET,
            re.compile(URL),
            json={"workflow_runs": []},
            status=200,
        )

        result = fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: "abc123"})

        assert result == {}

    def test_should_skip_pr_without_sha(self):
        result = fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: None})

        assert result == {}

    @responses.activate
    def test_should_send_head_sha_param(self):
        responses.add(
            responses.GET,
            re.compile(URL + r"\?head_sha=abc123&per_page=100"),
            json={"workflow_runs": [_run("completed", "success")]},
            status=200,
            match_querystring=True,
        )

        result = fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: "abc123"})

        assert result == {1: "SUCCESS"}

    @responses.activate
    def test_should_raise_auth_error_on_403(self):
        responses.add(responses.GET, re.compile(URL), status=403)

        with pytest.raises(GitHubAuthError, match="needs Actions: Read"):
            fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: "abc123"})

    @responses.activate
    def test_should_raise_not_found_on_404(self):
        responses.add(responses.GET, re.compile(URL), status=404)

        with pytest.raises(GitHubNotFoundError):
            fetch_open_pr_build_state("fake-token", "myorg", "myrepo", {1: "abc123"})

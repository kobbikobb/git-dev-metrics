"""Tests for token validation and classic-PAT rejection."""

import requests
import responses

from git_dev_metrics.github.auth_cache import token_error


class TestTokenError:
    @responses.activate
    def test_should_accept_fine_grained_token(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={"login": "dev1"},
            status=200,
        )

        assert token_error("fine-grained-token") is None

    @responses.activate
    def test_should_reject_classic_token_with_scopes(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={"login": "dev1"},
            status=200,
            headers={"x-oauth-scopes": "repo, workflow"},
        )

        error = token_error("classic-token")

        assert error is not None
        assert "Classic PATs are not supported" in error

    @responses.activate
    def test_should_reject_invalid_token(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            json={"message": "Bad credentials"},
            status=401,
        )

        error = token_error("bad-token")

        assert error is not None
        assert "Invalid token" in error

    @responses.activate
    def test_should_reject_on_server_error(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            status=500,
        )

        error = token_error("token")

        assert error is not None
        assert "Invalid token" in error

    @responses.activate
    def test_should_report_connection_error(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user",
            body=requests.ConnectionError("boom"),
        )

        error = token_error("token")

        assert error is not None
        assert "Could not reach GitHub" in error

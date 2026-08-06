from contextlib import suppress

import keyring
import requests

SERVICE_NAME = "github-dev-metrics"
TOKEN_KEY = "github_token"


def save_token(token: str) -> None:
    """Save token to system keyring."""
    keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)


def load_token() -> str | None:
    """Load token from system keyring."""
    with suppress(Exception):
        return keyring.get_password(SERVICE_NAME, TOKEN_KEY)
    return None


def token_error(token: str) -> str | None:
    """Return an error message if the token is unusable, else None.

    Rejects invalid tokens and classic PATs: only fine-grained tokens are
    supported. Classic PATs are detected via the `x-oauth-scopes` response
    header, which classic tokens populate and fine-grained tokens leave empty.
    """
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
            timeout=10,
        )
    except requests.RequestException:
        return "Could not reach GitHub to validate the token."
    if response.status_code != 200:
        return "Invalid token. Please check your PAT and try again."
    if response.headers.get("x-oauth-scopes", "").strip():
        return (
            "Classic PATs are not supported — create a fine-grained token at "
            "https://github.com/settings/tokens?type=beta"
        )
    return None


def delete_token() -> None:
    """Delete token from system keyring."""
    with suppress(Exception):
        keyring.delete_password(SERVICE_NAME, TOKEN_KEY)

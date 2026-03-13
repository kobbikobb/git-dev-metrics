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


def is_token_valid(token: str) -> bool:
    """Check if the token is valid by making a test API call."""
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {token}"},
    )
    return response.status_code == 200


def delete_token() -> None:
    """Delete token from system keyring."""
    with suppress(Exception):
        keyring.delete_password(SERVICE_NAME, TOKEN_KEY)

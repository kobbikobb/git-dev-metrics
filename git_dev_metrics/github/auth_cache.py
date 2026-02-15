from functools import wraps

import keyring
import requests

SERVICE_NAME = "github-dev-metrics"
TOKEN_KEY = "github_token"


def _save_token(token: str) -> None:
    """Save token to system keyring."""
    keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)


def _find_token() -> str | None:
    """Load token from system keyring."""
    try:
        return keyring.get_password(SERVICE_NAME, TOKEN_KEY)
    except Exception:
        return None


def _is_token_valid(token: str) -> bool:
    """Check if the token is valid by making a test API call."""
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {token}"},
    )
    return response.status_code == 200


def with_cached_token(func):
    """Decorator to cache and validate GitHub tokens."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        cached_token = _find_token()
        if cached_token and _is_token_valid(cached_token):
            return cached_token

        token = func(*args, **kwargs)

        _save_token(token)
        return token

    return wrapper

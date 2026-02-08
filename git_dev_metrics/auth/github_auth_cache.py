import keyring
from typing import Optional
from functools import wraps

SERVICE_NAME = "github-dev-metrics"
TOKEN_KEY = "github_token"


def save_token(token: str) -> None:
    """Save token to system keyring."""
    keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)


def find_token() -> Optional[str]:
    """Load token from system keyring."""
    try:
        return keyring.get_password(SERVICE_NAME, TOKEN_KEY)
    except Exception:
        return None


def with_cached_token(func):
    """Decorator to cache and validate GitHub tokens."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        cached_token = find_token()
        if cached_token:
            return cached_token

        token = func(*args, **kwargs)

        save_token(token)
        return token

    return wrapper

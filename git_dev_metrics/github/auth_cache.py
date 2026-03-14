from contextlib import suppress

import keyring
import requests

SERVICE_NAME = "github-dev-metrics"
TOKEN_KEY = "github_token"
ORG_KEY = "last_org"
PERIOD_KEY = "last_period"


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


def save_last_org(org: str) -> None:
    """Save last selected org to system keyring."""
    keyring.set_password(SERVICE_NAME, ORG_KEY, org)


def load_last_org() -> str | None:
    """Load last selected org from system keyring."""
    with suppress(Exception):
        return keyring.get_password(SERVICE_NAME, ORG_KEY)
    return None


def save_last_period(period: str) -> None:
    """Save last selected period to system keyring."""
    keyring.set_password(SERVICE_NAME, PERIOD_KEY, period)


def load_last_period() -> str | None:
    """Load last selected period from system keyring."""
    with suppress(Exception):
        return keyring.get_password(SERVICE_NAME, PERIOD_KEY)
    return None

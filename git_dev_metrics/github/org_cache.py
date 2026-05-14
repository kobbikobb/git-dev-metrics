from contextlib import suppress

import keyring

SERVICE_NAME = "github-dev-metrics"
ORG_KEY = "last_org"


def save_last_org(org: str) -> None:
    """Save last selected org to system keyring."""
    keyring.set_password(SERVICE_NAME, ORG_KEY, org)


def load_last_org() -> str | None:
    """Load last selected org from system keyring."""
    with suppress(Exception):
        return keyring.get_password(SERVICE_NAME, ORG_KEY)
    return None

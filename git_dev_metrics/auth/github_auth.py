import requests
import time
import webbrowser
from typing import TypedDict

from .github_auth_cache import with_cached_token
from ..type_definitions import GitHubAuthError

CLIENT_ID = "Iv23libjj9FWqHhZzWik"
DEVICE_CODE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"


class DeviceCodeResponse(TypedDict):
    device_code: str
    user_code: str
    verification_uri: str
    interval: int
    expires_in: int


class TokenResponse(TypedDict, total=False):
    access_token: str
    error: str
    error_description: str


def request_device_code() -> DeviceCodeResponse:
    """Request device code and verification URL from GitHub."""
    return requests.post(
        DEVICE_CODE_URL,
        data={"client_id": CLIENT_ID},
        headers={"Accept": "application/json"},
    ).json()


def prompt_user(verification_uri: str, user_code: str) -> None:
    """Display code and open browser for user authorization."""
    print(f"Go to {verification_uri} and enter: {user_code}")
    webbrowser.open(verification_uri)


def poll_for_token(device_code: str, poll_interval: int) -> str:
    """Poll GitHub until token is granted."""
    while True:
        time.sleep(poll_interval)

        token_response: TokenResponse = requests.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        ).json()

        if "access_token" in token_response:
            return token_response["access_token"]

        error = token_response.get("error")
        if error == "slow_down":
            poll_interval += 5
        elif error != "authorization_pending":
            raise GitHubAuthError(f"OAuth failed: {error}")


@with_cached_token
def get_github_token() -> str:
    """Get GitHub token using device flow."""
    device_response = request_device_code()
    prompt_user(device_response["verification_uri"], device_response["user_code"])

    return poll_for_token(
        device_response["device_code"], device_response.get("interval", 5)
    )

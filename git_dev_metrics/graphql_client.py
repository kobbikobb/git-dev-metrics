import requests
from .types import GitHubAPIError, GitHubRateLimitError

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_API_VERSION = "2022-11-28"


def get_graphql_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


class GitHubGraphQL:
    def __init__(self, token: str):
        self.token = token

    def execute(self, query: str, variables: dict | None = None) -> dict:
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            GITHUB_GRAPHQL_URL,
            headers=get_graphql_headers(self.token),
            json=payload,
        )

        if response.status_code == 401:
            raise GitHubAPIError("Unauthorized. Your token might be expired.")

        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                raise GitHubRateLimitError(
                    "Rate limit exceeded. Please try again later."
                )
            raise GitHubAPIError("Forbidden. Check your token permissions.")

        if response.status_code == 502:
            raise GitHubAPIError("Bad gateway. GitHub GraphQL API may be unavailable.")

        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            error_messages = [e["message"] for e in data["errors"]]
            raise GitHubAPIError(f"GraphQL errors: {', '.join(error_messages)}")

        return data

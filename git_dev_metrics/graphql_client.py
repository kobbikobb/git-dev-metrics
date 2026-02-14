import requests
from .types import GitHubAPIError, GitHubRateLimitError

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_TIMEOUT = 30  # seconds

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
        
        try:
            response = requests.post(
                GITHUB_GRAPHQL_URL,
                headers=get_graphql_headers(self.token),
                json=payload,
                timeout=DEFAULT_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            raise GitHubAPIError(f"Network error: {str(e)}")
        
        # Check rate limit headers
        if response.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubRateLimitError(
                "Rate limit exceeded. Please try again later."
            )
        
        if response.status_code == 401:
            raise GitHubAPIError("Unauthorized. Your token might be expired.")
        
        if response.status_code == 403:
            raise GitHubAPIError("Forbidden. Check your token permissions.")
        
        if response.status_code == 502:
            raise GitHubAPIError("Bad gateway. GitHub GraphQL API may be unavailable.")
        
        if not response.ok:
            raise GitHubAPIError(f"HTTP {response.status_code}: {response.text}")
        
        data = response.json()
        
        if "errors" in data:
            error_messages = [e["message"] for e in data["errors"]]
            raise GitHubAPIError(f"GraphQL errors: {', '.join(error_messages)}")
        
        return data

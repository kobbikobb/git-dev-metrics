from typing import Any

from gql import Client
from gql.graphql_request import GraphQLRequest
from gql.transport import exceptions as transport_exceptions
from gql.transport.requests import RequestsHTTPTransport

from .exceptions import GitHubAPIError, GitHubAuthError, GitHubNotFoundError, GitHubRateLimitError

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

DEFAULT_PAGE_SIZE = 100


def get_client(token: str) -> Client:
    """Create a GraphQL client with the given token."""
    transport = RequestsHTTPTransport(
        url=GITHUB_GRAPHQL_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    return Client(transport=transport)


def execute_query(
    client: Client, query: GraphQLRequest, variables: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a GraphQL query and handle errors."""
    try:
        result = client.execute(query, variable_values=variables)
        return result if result is not None else {}
    except transport_exceptions.TransportQueryError as e:
        _handle_graphql_error(e)
        return {}  # unreachable but needed for type checker
    except transport_exceptions.TransportConnectionFailed as e:
        raise GitHubAPIError(f"Network error: {e}") from e
    except Exception as e:
        raise GitHubAPIError(f"GitHub API error: {e}") from e


def _handle_graphql_error(e: transport_exceptions.TransportQueryError) -> None:
    """Map GraphQL errors to custom exceptions."""
    if not e.errors:
        raise GitHubAPIError("Unknown GraphQL error") from e

    for error in e.errors:
        message = error.get("message", "")
        error_type = error.get("type", "")

        if error_type in ("FORBIDDEN", "UNAUTHORIZED") or "authentication" in message.lower():
            raise GitHubAuthError("Unauthorized. Your token might be expired.") from e

        if error_type == "NOT_FOUND" or "Not Found" in message:
            raise GitHubNotFoundError(message) from e

        if "rate limit" in message.lower():
            raise GitHubRateLimitError("Rate limit exceeded") from e

    raise GitHubAPIError(e.errors[0].get("message", "GraphQL error"))


def execute_paginated_query(
    client: Client,
    query: GraphQLRequest,
    variables: dict[str, Any],
    path: str,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> list[dict[str, Any]]:
    """
    Execute a paginated GraphQL query and return all results.

    Args:
        client: GraphQL client
        query: GraphQL query
        variables: Query variables (will be modified with after/cursor)
        path: Dot-separated path to the nodes in the response (e.g., "repository.pullRequests")
        page_size: Number of items per page

    Returns:
        List of all nodes fetched across all pages
    """
    all_nodes = []
    variables_copy = {**variables, "first": page_size}
    cursor = None

    while True:
        if cursor:
            variables_copy["after"] = cursor
        else:
            variables_copy.pop("after", None)

        result = execute_query(client, query, variables_copy)

        # Navigate to the nodes using the path
        current: Any = result
        keys = path.split(".")

        for i, key in enumerate(keys):
            if isinstance(current, dict):
                current = current.get(key, {})
                # After getting a dict, check if it has "nodes" - that's the list we want
                if isinstance(current, dict) and "nodes" in current:
                    # If this is the last key in the path, we want the nodes
                    if i == len(keys) - 1:
                        current = current.get("nodes", [])
                    else:
                        # Otherwise, continue navigating
                        current = current.get("nodes", [])
            elif isinstance(current, list):
                # If we hit a list, we're done with the path
                break

        if isinstance(current, list):
            all_nodes.extend(current)

        # Get page info to check for more pages
        page_info = result
        for key in path.split("."):
            page_info = page_info.get(key, {})

        has_next_page = page_info.get("hasNextPage", False)
        if not has_next_page:
            break

        cursor = page_info.get("endCursor")
        if not cursor:
            break

    return all_nodes

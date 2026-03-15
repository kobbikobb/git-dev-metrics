import logging
import time
from collections.abc import Callable
from typing import Any

from gql import Client
from gql.graphql_request import GraphQLRequest
from gql.transport import exceptions as transport_exceptions
from gql.transport.requests import RequestsHTTPTransport
from rich.console import Console
from rich.live import Live

from .exceptions import GitHubAPIError, GitHubAuthError, GitHubNotFoundError, GitHubRateLimitError

logger = logging.getLogger(__name__)
console = Console()

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

DEFAULT_PAGE_SIZE = 50
DEFAULT_TIMEOUT = 60


def get_client(token: str) -> Client:
    """Create a GraphQL client with the given token."""
    transport = RequestsHTTPTransport(
        url=GITHUB_GRAPHQL_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=DEFAULT_TIMEOUT,
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


def _extract_nodes(result: dict[str, Any], path: str) -> list[dict[str, Any]]:
    """Extract nodes from a GraphQL result following the given path."""
    current: Any = result
    keys = path.split(".")

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, {})
            if isinstance(current, dict) and "nodes" in current:
                current = current.get("nodes", [])
        elif isinstance(current, list):
            break

    return current if isinstance(current, list) else []


def _get_page_info(result: dict[str, Any], path: str) -> dict[str, Any]:
    """Extract page info from a GraphQL result following the given path."""
    page_info: Any = result
    for key in path.split("."):
        page_info = page_info.get(key, {})
    return page_info if isinstance(page_info, dict) else {}


def _fetch_page(
    client: Client,
    query: GraphQLRequest,
    variables_copy: dict[str, Any],
    cursor: str | None,
    path: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch a single page and return nodes + next cursor."""
    if cursor:
        variables_copy["after"] = cursor
    else:
        variables_copy.pop("after", None)

    result = execute_query(client, query, variables_copy)
    nodes = _extract_nodes(result, path)
    page_info = _get_page_info(result, path)

    next_cursor = page_info.get("endCursor") if page_info.get("hasNextPage") else None
    return nodes, next_cursor


def execute_paginated_query(
    client: Client,
    query: GraphQLRequest,
    variables: dict[str, Any],
    path: str,
    page_size: int | None = None,
    stop_if: Callable[[dict[str, Any]], bool] | None = None,
) -> list[dict[str, Any]]:
    """Execute a paginated GraphQL query and return all results."""
    owner = variables.get("owner", "")
    name = variables.get("name", "")
    repo_id = f"{owner}/{name}" if owner and name else path

    all_nodes = []
    variables_copy = {**variables}
    if page_size is not None:
        variables_copy["first"] = page_size
    cursor = None
    page_num = 0

    spinner_idx = 0

    with Live(console=console, transient=True, refresh_per_second=10) as live:
        live.update(f"[bold blue]{SPINNER_FRAMES[0]}[/bold blue] Fetching {repo_id}...")

        while True:
            start = time.perf_counter()
            nodes, cursor = _fetch_page(client, query, variables_copy, cursor, path)
            elapsed = time.perf_counter() - start

            page_num += 1
            spinner_idx = (spinner_idx + 1) % len(SPINNER_FRAMES)
            live.update(
                f"[bold blue]{SPINNER_FRAMES[spinner_idx]}[/bold blue] "
                f"Fetching {repo_id}... page {page_num} ({len(all_nodes)} items, {elapsed:.1f}s)"
            )

            for node in nodes:
                if stop_if and stop_if(node):
                    console.print(f"[green]✓[/green] {repo_id}: {len(all_nodes)} PRs")
                    return all_nodes
                all_nodes.append(node)
            if not cursor:
                break

    console.print(f"[green]✓[/green] {repo_id}: {len(all_nodes)} items")
    return all_nodes

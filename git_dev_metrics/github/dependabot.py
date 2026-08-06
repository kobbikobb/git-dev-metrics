"""Dependabot alerts via REST — authoritative vulnerability severity per PR.

Narrow exception to ADR-0003 (GraphQL over REST): the severity data only
exists on the Dependabot alerts REST endpoint and the GraphQL alternative
has an unreliable link field. Scoped to this one fetch; do not grow this
into a general REST client.
"""

from collections.abc import Mapping

import requests

from ..models import SecurityInfo
from .exceptions import GitHubAPIError, GitHubAuthError, GitHubNotFoundError

DEPENDABOT_ALERTS_URL = "https://api.github.com/repos/{org}/{repo}/dependabot/alerts"
DEFAULT_TIMEOUT = 60
PAGE_SIZE = 100


def _link_next(headers: Mapping[str, str] | None) -> str | None:
    """Extract the next-page URL from a Link header, if present."""
    if headers is None:
        return None
    link = headers.get("Link", "")
    for part in link.split(","):
        if 'rel="next"' in part:
            url = part[part.find("<") + 1 : part.find(">")]
            return url or None
    return None


def _map_alerts(alerts: list[dict]) -> dict[int, SecurityInfo]:
    """Map alert payloads to {pull_request_number: SecurityInfo}."""
    result: dict[int, SecurityInfo] = {}
    for alert in alerts:
        update = alert.get("dependabot_update") or {}
        pr_number = update.get("pull_request_number")
        advisory = alert.get("security_advisory") or {}
        severity = advisory.get("severity")
        if pr_number is None or severity is None:
            continue
        result[pr_number] = {
            "severity": severity,
            "advisory_id": advisory.get("ghsa_id") or advisory.get("cve_id") or "",
        }
    return result


def fetch_open_pr_security(token: str, org: str, repo: str) -> dict[int, SecurityInfo]:
    """Fetch open Dependabot alerts for a repo, keyed by pull request number.

    Raises:
        GitHubNotFoundError: repo not found or alerts not available.
        GitHubAuthError: token lacks permission to read security alerts.
        GitHubAPIError: request failed.
    """
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    url = DEPENDABOT_ALERTS_URL.format(org=org, repo=repo)
    alerts: list[dict] = []
    while url:
        response = session.get(
            url,
            params={"state": "open", "per_page": PAGE_SIZE},
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code == 404:
            raise GitHubNotFoundError(f"Repo {org}/{repo} not found or security alerts unavailable")
        if response.status_code in (401, 403):
            raise GitHubAuthError(
                f"Token cannot read security alerts for {org}/{repo} "
                "(needs Dependabot alerts: Read permission)"
            )
        if response.status_code >= 400:
            raise GitHubAPIError(
                f"Failed to fetch Dependabot alerts for {org}/{repo}: HTTP {response.status_code}"
            )
        alerts.extend(response.json())
        url = _link_next(response.headers)
    return _map_alerts(alerts)

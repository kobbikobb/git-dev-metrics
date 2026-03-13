import logging

from ..github import GitHubError, get_github_token
from ..metrics import get_combined_metrics, get_recent_repositories
from .prompts import prompt_repo_selection

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Failed during analysis (auth, fetch, etc)."""

    pass


def _fetch_stale_prs(token: str, selected: list[str]) -> list[dict]:
    """Fetch stale PRs from all selected repositories."""
    from ..github import GitHubError
    from ..github.queries import fetch_open_prs
    from ..metrics.calculator import get_stale_prs

    stale_prs = []
    for full_repo in selected:
        org, repo_name = full_repo.split("/")
        try:
            open_prs = fetch_open_prs(token, org, repo_name)
            stale_prs.extend(get_stale_prs(open_prs, repo_name))
        except GitHubError as e:
            logger.warning("Could not fetch stale PRs for %s: %s", full_repo, e)
    return stale_prs


def run_analyze(
    org: str | None, repo: str | None, period: str, output_path: str | None, verbose: bool
) -> None:
    """Orchestrate the full analyze flow."""
    from pathlib import Path

    from .output import print_metrics, print_stale_prs, resolve_output_path

    token = get_github_token()
    selected = (
        [f"{org}/{repo}"] if org and repo else prompt_repo_selection(get_recent_repositories(token))
    )

    try:
        metrics = get_combined_metrics(token, selected, period)
    except GitHubError as e:
        logger.error("Error fetching metrics: %s", e)
        if verbose:
            logger.exception("Full traceback:")
        raise AnalysisError(str(e)) from e

    resolved_path = resolve_output_path(Path(output_path) if output_path else None)
    print_metrics(metrics, period, resolved_path)

    stale_prs = _fetch_stale_prs(token, selected)
    if stale_prs:
        print_stale_prs(stale_prs, resolved_path)

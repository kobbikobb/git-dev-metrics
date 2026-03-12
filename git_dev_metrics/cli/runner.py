import logging

from ..github import GitHubError, get_github_token
from ..metrics import get_bottleneck_metrics, get_combined_metrics, get_recent_repositories
from .prompts import prompt_repo_selection

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Failed during analysis (auth, fetch, etc)."""

    pass


def run_analyze(
    org: str | None,
    repo: str | None,
    period: str,
    output_path: str | None,
    verbose: bool,
) -> None:
    """
    Orchestrate the full analyze flow.
    Raises AnalysisError on failure.
    """
    token = get_github_token()

    if org is not None and repo is not None:
        selected = [f"{org}/{repo}"]
    else:
        repos = get_recent_repositories(token)
        selected = prompt_repo_selection(repos)

    try:
        metrics = get_combined_metrics(token, selected, period)
    except GitHubError as e:
        logger.error("Error fetching metrics: %s", e)
        if verbose:
            logger.exception("Full traceback:")
        raise AnalysisError(str(e)) from e

    from pathlib import Path

    from .output import print_bottlenecks, print_metrics, resolve_output_path

    resolved_path = resolve_output_path(Path(output_path) if output_path else None)
    print_metrics(metrics, period, resolved_path)

    try:
        bottleneck_data = get_bottleneck_metrics(token, selected)
        print_bottlenecks(bottleneck_data, resolved_path)
    except GitHubError as e:
        logger.warning("Could not fetch bottleneck data: %s", e)

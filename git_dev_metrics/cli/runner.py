import logging
from pathlib import Path

from ..github import (
    GitHubError,
    fetch_org_repositories,
    fetch_organizations,
    fetch_repositories,
    get_github_token,
    load_last_org,
    save_last_org,
)
from ..metrics import get_combined_metrics
from .output import print_metrics, print_stale_prs, resolve_output_path
from .prompts import prompt_org_selection, prompt_repo_selection

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Failed during analysis (auth, fetch, etc)."""

    pass


def _fetch_stale_prs(token: str, selected: list[str]) -> list[dict]:
    """Fetch stale PRs from all selected repositories."""
    from ..github import fetch_open_prs as _fetch_open_prs
    from ..metrics.calculator import get_stale_prs

    stale_prs = []
    for full_repo in selected:
        org, repo_name = full_repo.split("/")
        try:
            open_prs = _fetch_open_prs(token, org, repo_name)
            stale_prs.extend(get_stale_prs(open_prs, full_repo))
        except GitHubError as e:
            logger.warning("Could not fetch stale PRs for %s: %s", full_repo, e)
    return stale_prs


def run_analyze(
    period: str,
    output: Path | None,
) -> None:
    """
    Orchestrate the full analyze flow.
    Raises AnalysisError on failure.
    """
    token = get_github_token()

    organizations = fetch_organizations(token)

    if organizations:
        last_org = load_last_org()
        selected_org = prompt_org_selection(organizations, last_org)
        save_last_org(selected_org)
        repos = fetch_org_repositories(token, selected_org)
    else:
        repos = fetch_repositories(token)

    repo_options = {repo["full_name"]: "Private" if repo["private"] else "Public" for repo in repos}
    selected = prompt_repo_selection(repo_options)

    try:
        metrics = get_combined_metrics(token, selected, period)
    except GitHubError as e:
        raise AnalysisError(str(e)) from e

    output_path = resolve_output_path(output)
    print_metrics(metrics, period, output_path)

    stale_prs = _fetch_stale_prs(token, selected)
    if stale_prs:
        print_stale_prs(stale_prs, output_path)

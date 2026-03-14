import logging
from pathlib import Path

from ..github import (
    GitHubError,
    fetch_org_repositories,
    get_github_token,
    load_last_org,
    load_last_period,
    save_last_org,
    save_last_period,
)
from ..metrics import get_combined_metrics
from ..utils import parse_time_period
from .output import (
    print_metrics,
    print_stale_prs,
    resolve_output_path,
)
from .prompts import (
    prompt_org_name,
    prompt_period_selection,
    prompt_repo_selection,
)

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

    stale_prs.sort(key=lambda x: x["age_hours"], reverse=True)
    return stale_prs


def _filter_repos_by_period(repos: list, since) -> list:
    """Filter repos to only those with recent pushes."""
    return [repo for repo in repos if repo.get("last_pushed") and repo["last_pushed"] >= since]


def run_analyze(
    output: Path | None,
    org: str | None = None,
    repo: str | None = None,
    period: str | None = None,
) -> None:
    """
    Orchestrate the full analyze flow.
    Raises AnalysisError on failure.
    """
    token = get_github_token()

    last_period = load_last_period()
    last_org = load_last_org()

    selected_org = org if org is not None else prompt_org_name(last_org)
    save_last_org(selected_org)

    period = period if period is not None else prompt_period_selection(last_period or "30d")
    save_last_period(period)

    repos = fetch_org_repositories(token, selected_org)

    since = parse_time_period(period)
    repos = _filter_repos_by_period(repos, since)

    repo_options = {repo["full_name"]: "Private" if repo["private"] else "Public" for repo in repos}

    if repo is not None:
        full_name = f"{selected_org}/{repo}"
        selected = [full_name] if full_name in repo_options else [full_name]
    else:
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

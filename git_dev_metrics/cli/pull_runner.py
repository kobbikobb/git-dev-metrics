from collections.abc import Callable
from pathlib import Path

from ..cache import insert_prs, seal_month
from ..github.queries import fetch_repo_metrics
from ..models import PullRequest
from ..utils.date_utils import TimePeriod


def fetch_and_seal_month(
    org: str,
    repo: str,
    year: int,
    month: int,
    period: TimePeriod,
    token: str,
    db_path: Path | None,
    fetch: Callable[..., list[PullRequest]] | None = None,
) -> int:
    """Fetch a month of PRs for one repo, upsert into the cache, seal it, return PR count."""
    prs = (fetch or fetch_repo_metrics)(token, org, repo, period)
    insert_prs(prs, org, repo, year, month, db_path=db_path)
    seal_month(org, repo, year, month, db_path=db_path)
    return len(prs)

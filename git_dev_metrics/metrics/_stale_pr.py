"""Typed stale-PR data and detection logic."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from ..models import OpenPullRequest

STALE_PR_THRESHOLD_HOURS = 24 * 7  # 7 days


@dataclass(frozen=True)
class StalePr:
    number: int
    title: str
    author: str | None
    repo: str
    age_hours: float
    age_days: float
    is_draft: bool
    is_approved: bool
    url: str


def _calculate_age_hours(
    created_at: datetime | None, clock: Callable[[], datetime] | None = None
) -> float:
    from datetime import UTC, datetime

    now = clock() if clock else datetime.now(UTC)
    if created_at is None:
        return 0.0
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return (now - created_at).total_seconds() / 3600


def _is_stale_pr(
    pr: OpenPullRequest, repo: str, clock: Callable[[], datetime] | None = None
) -> StalePr | None:
    created = pr.get("created_at")
    if created is None:
        return None

    age_hours = _calculate_age_hours(created, clock)
    if age_hours > STALE_PR_THRESHOLD_HOURS:
        number = pr.get("number")
        return StalePr(
            number=number if number is not None else 0,
            title=pr.get("title") or "",
            author=pr.get("user", {}).get("login"),
            repo=repo,
            age_hours=round(age_hours, 1),
            age_days=round(age_hours / 24, 1),
            is_draft=pr.get("is_draft", False),
            is_approved=pr.get("is_approved", False),
            url=f"https://github.com/{repo}/pull/{number}",
        )
    return None


def get_stale_prs(
    prs: list[OpenPullRequest], repo: str = "", clock: Callable[[], datetime] | None = None
) -> list[StalePr]:
    stale = [p for p in (_is_stale_pr(pr, repo, clock) for pr in prs) if p]
    stale.sort(key=lambda x: x.age_hours, reverse=True)
    return stale


def summarize_stale_prs(stale_prs: list[StalePr]) -> tuple[int, float]:
    total = len(stale_prs)
    avg_age = sum(pr.age_days for pr in stale_prs) / total if stale_prs else 0.0
    return total, round(avg_age, 1)

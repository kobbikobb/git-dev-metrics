from collections.abc import Sequence
from dataclasses import dataclass

from ..constants import is_bot_login
from ..models import PullRequest
from ..utils.date_utils import month_key, month_label


@dataclass(frozen=True)
class TeamVelocityMonth:
    month_label: str
    month_key: str
    pr_count: int
    active_devs: int
    prs_per_dev: float


@dataclass(frozen=True)
class TeamVelocityDataset:
    months: list[TeamVelocityMonth]
    dev_month_counts: list[dict[str, int]]


def _count_active_devs(prs: Sequence[PullRequest]) -> int:
    return len({pr["user"]["login"] for pr in prs if not is_bot_login(pr["user"]["login"])})


def _latest_active_devs(
    months: list[tuple[int, int]], prs_per_month: dict[tuple[int, int], list[PullRequest]]
) -> set[str]:
    for y, m in reversed(months):
        month_prs = prs_per_month.get((y, m), [])
        if month_prs:
            return {
                pr["user"]["login"] for pr in month_prs if not is_bot_login(pr["user"]["login"])
            }
    return set()


def _dev_month_counts(
    months: list[tuple[int, int]], prs_per_month: dict[tuple[int, int], list[PullRequest]]
) -> list[dict[str, int]]:
    all_devs = sorted(_latest_active_devs(months, prs_per_month))
    result: list[dict[str, int]] = []
    for y, m in months:
        month_prs = prs_per_month.get((y, m), [])
        if not month_prs:
            continue
        counts: dict[str, int] = {dev: 0 for dev in all_devs}
        for pr in month_prs:
            login = pr["user"]["login"]
            if login in counts:
                counts[login] += 1
        result.append(counts)
    return result


def build_team_velocity_dataset(
    months: list[tuple[int, int]],
    prs_per_month: dict[tuple[int, int], list[PullRequest]],
) -> TeamVelocityDataset:
    """Per-month total PR count, active developer count, and PRs per dev."""
    rows: list[TeamVelocityMonth] = []
    for y, m in months:
        month_prs = prs_per_month.get((y, m), [])
        if not month_prs:
            continue
        pr_count = len(month_prs)
        active = _count_active_devs(month_prs)
        rows.append(
            TeamVelocityMonth(
                month_label=month_label(y, m),
                month_key=month_key(y, m),
                pr_count=pr_count,
                active_devs=active,
                prs_per_dev=round(pr_count / active, 1) if active else 0.0,
            )
        )
    dev_counts = _dev_month_counts(months, prs_per_month)
    return TeamVelocityDataset(months=rows, dev_month_counts=dev_counts)


__all__ = ["TeamVelocityDataset", "TeamVelocityMonth", "build_team_velocity_dataset"]

from collections.abc import Sequence
from dataclasses import dataclass

from ..constants import is_bot_login
from ..models import PullRequest
from ..utils.date_utils import month_label


@dataclass(frozen=True)
class TeamVelocityDataset:
    months: list[str]
    repos: list[str]
    repo_pr_counts: dict[str, list[int]]
    active_devs: list[int]
    prs_per_dev: list[float]


def _count_active_devs(prs: Sequence[PullRequest]) -> int:
    return len({pr["user"]["login"] for pr in prs if not is_bot_login(pr["user"]["login"])})


def _active_months(
    repo_prs_by_month: dict[str, dict[tuple[int, int], list[PullRequest]]],
) -> list[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    for repo_data in repo_prs_by_month.values():
        seen.update(repo_data)
    return sorted(seen)


def _all_prs_for_month(
    ym: tuple[int, int],
    repos: list[str],
    repo_prs_by_month: dict[str, dict[tuple[int, int], list[PullRequest]]],
) -> list[PullRequest]:
    out: list[PullRequest] = []
    for repo in repos:
        out.extend(repo_prs_by_month[repo].get(ym, []))
    return out


def build_team_velocity_dataset(
    repo_prs_by_month: dict[str, dict[tuple[int, int], list[PullRequest]]],
) -> TeamVelocityDataset:
    """Per-repo and aggregate per-month team velocity data."""
    ordered_months = _active_months(repo_prs_by_month)
    if not ordered_months:
        return TeamVelocityDataset(
            months=[],
            repos=[],
            repo_pr_counts={},
            active_devs=[],
            prs_per_dev=[],
        )

    repos = sorted(repo_prs_by_month)
    month_labels = [month_label(y, m) for y, m in ordered_months]

    repo_pr_counts: dict[str, list[int]] = {}
    for repo in repos:
        repo_pr_counts[repo] = [len(repo_prs_by_month[repo].get(ym, [])) for ym in ordered_months]

    active_devs: list[int] = []
    prs_per_dev: list[float] = []
    for ym in ordered_months:
        all_prs = _all_prs_for_month(ym, repos, repo_prs_by_month)
        pr_count = len(all_prs)
        active = _count_active_devs(all_prs)
        active_devs.append(active)
        prs_per_dev.append(round(pr_count / active, 1) if active else 0.0)

    return TeamVelocityDataset(
        months=month_labels,
        repos=repos,
        repo_pr_counts=repo_pr_counts,
        active_devs=active_devs,
        prs_per_dev=prs_per_dev,
    )


__all__ = ["TeamVelocityDataset", "build_team_velocity_dataset"]

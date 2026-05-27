import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from ..constants import is_bot_login
from ..models import PullRequest


@dataclass(frozen=True)
class DevMonthRow:
    month_label: str
    month_key: str
    pr_count: int
    cycle_hours: float
    ai_pct: float


class DevMonthDict(TypedDict):
    month_label: str
    month_key: str
    pr_count: int
    cycle_hours: float
    ai_pct: float


@dataclass(frozen=True)
class TrendDataset:
    months: list[str]
    devs: list[str]
    rows: dict[str, list[DevMonthRow]]


def _month_label(year: int, month: int) -> str:
    return datetime(year, month, 1).strftime("%b %Y")


def _month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _active_devs(prs: list[PullRequest]) -> set[str]:
    return {pr["user"]["login"] for pr in prs if not is_bot_login(pr["user"]["login"])}


def _median(values: Sequence[float | int]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    return sorted_values[n // 2]


def _pr_start_time(pr: PullRequest) -> datetime | None:
    created = pr["created_at"]
    if created is None:
        return None
    first_commit = pr.get("first_commit_at")
    start = first_commit if first_commit is not None and first_commit < created else created
    ready_for_review = pr.get("ready_for_review_at")
    if ready_for_review is not None and ready_for_review > start:
        start = ready_for_review
    return start


def _first_approval_at(pr: PullRequest) -> datetime | None:
    for review in pr.get("reviews", []):
        if review.get("state") == "APPROVED":
            return review.get("submitted_at")
    return None


def _median_cycle_hours(prs: list[PullRequest]) -> float:
    if not prs:
        return 0.0
    hours = []
    for pr in prs:
        merged = pr["merged_at"]
        start_time = _pr_start_time(pr)
        if start_time is None or merged is None:
            continue
        if _first_approval_at(pr) is None:
            continue
        hours.append((merged - start_time).total_seconds() / 3600)
    return round(_median(hours), 2) if hours else 0.0


_AI_PATTERNS = [
    r"Co-Authored-By:",
    r"co-authored-by:",
    r"Generated\s+(by|with|with\s+)?[\w\s]*AI",
    r"Claude\s+Code",
    r"Coding-Agent:",
    r"AI-assistant:",
    r"🤖\s*Generated",
    r"Aider:",
    r"Cursor:",
    r"GitHub\s+Copilot:",
    r"Devin:",
]


def _is_ai_coauthored(pr: PullRequest) -> bool:
    texts = [pr.get("body") or "", *(pr.get("commit_messages") or [])]
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for text in texts
        if text
        for pattern in _AI_PATTERNS
    )


def _ai_percentage(prs: list[PullRequest]) -> float:
    if not prs:
        return 0.0
    ai_count = sum(1 for pr in prs if _is_ai_coauthored(pr))
    return round((ai_count / len(prs)) * 100, 1)


def _row(dev: str, year: int, month: int, prs: list[PullRequest]) -> DevMonthRow:
    dev_prs = [pr for pr in prs if pr["user"]["login"] == dev]
    return DevMonthRow(
        month_label=_month_label(year, month),
        month_key=_month_key(year, month),
        pr_count=len(dev_prs),
        cycle_hours=_median_cycle_hours(dev_prs),
        ai_pct=_ai_percentage(dev_prs),
    )


def build_trend_dataset(
    months: list[tuple[int, int]],
    prs_per_month: dict[tuple[int, int], list[PullRequest]],
) -> TrendDataset:
    """Per-(dev, month) PR counts, cycle time and AI percentage, filtered to latest-month devs."""
    if not months:
        return TrendDataset(months=[], devs=[], rows={})

    latest = months[-1]
    active = _active_devs(prs_per_month.get(latest, []))
    devs = sorted(active)

    rows = {
        dev: [
            _row(dev, year, month, prs_per_month.get((year, month), [])) for year, month in months
        ]
        for dev in devs
    }
    return TrendDataset(months=[_month_key(y, m) for y, m in months], devs=devs, rows=rows)

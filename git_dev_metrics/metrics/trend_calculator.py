from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from ..constants import is_bot_login
from ..models import PullRequest
from ._ai_detection import calculate_ai_percentage
from .calculator import calculate_cycle_time


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


def _row(dev: str, year: int, month: int, prs: list[PullRequest]) -> DevMonthRow:
    dev_prs = [pr for pr in prs if pr["user"]["login"] == dev]
    return DevMonthRow(
        month_label=_month_label(year, month),
        month_key=_month_key(year, month),
        pr_count=len(dev_prs),
        cycle_hours=calculate_cycle_time(dev_prs),
        ai_pct=calculate_ai_percentage(dev_prs),
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

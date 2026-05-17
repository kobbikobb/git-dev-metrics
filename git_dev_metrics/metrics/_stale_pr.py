"""Typed stale-PR data from the stale-pr detection pipeline."""

from dataclasses import dataclass


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

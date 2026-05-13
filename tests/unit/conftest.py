from datetime import UTC, datetime
from typing import Any

import freezegun
import pytest

from git_dev_metrics.models import PullRequest

# default ignore list contains "gi" prefix which incorrectly skips git_dev_metrics modules
freezegun.configure(default_ignore_list=[])


@pytest.fixture(autouse=True)
def _stub_webbrowser(mocker):
    return mocker.patch("webbrowser.open", return_value=False)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def any_pr(**overrides: Any) -> PullRequest:
    """Create a PullRequest with sensible defaults for testing."""
    defaults: PullRequest = {
        "id": 1,
        "number": 1,
        "state": "merged",
        "title": "Test PR",
        "user": {"login": "dev1"},
        "created_at": _dt("2024-01-01T00:00:00Z"),
        "merged_at": _dt("2024-01-02T00:00:00Z"),
        "closed_at": _dt("2024-01-02T00:00:00Z"),
        "additions": 100,
        "deletions": 50,
        "changed_files": 5,
        "first_commit_at": None,
        "ready_for_review_at": None,
        "body": None,
        "commit_messages": [],
        "reviews": [],
    }
    return {**defaults, **overrides}  # type: ignore[return-value]


def approved_review(
    submitted_at: datetime | None = None, login: str = "reviewer"
) -> dict:
    """Approval review row for use in PullRequest fixtures."""
    if submitted_at is None:
        submitted_at = _dt("2024-01-01T12:00:00Z")
    return {"user": {"login": login}, "state": "APPROVED", "submitted_at": submitted_at}

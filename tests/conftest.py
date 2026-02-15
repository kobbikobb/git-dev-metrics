from typing import Any

from git_dev_metrics.models import PullRequest


def any_pr(**overrides: Any) -> PullRequest:
    """Create a PullRequest with sensible defaults for testing."""
    defaults: PullRequest = {
        "id": 1,
        "number": 1,
        "state": "merged",
        "title": "Test PR",
        "user": {"login": "dev1"},
        "created_at": "2024-01-01T00:00:00Z",
        "merged_at": "2024-01-02T00:00:00Z",
        "closed_at": "2024-01-02T00:00:00Z",
        "additions": 100,
        "deletions": 50,
        "changed_files": 5,
    }
    return {**defaults, **overrides}  # type: ignore[return-value]

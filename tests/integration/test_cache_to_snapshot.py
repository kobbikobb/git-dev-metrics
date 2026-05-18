"""Round-trip integration: PullRequest dicts → cache → load → MetricsSnapshot → Row.

Asserts the cache serialization round-trip (datetimes ↔ ISO strings, reviews ↔ DB rows,
JSON blobs) preserves enough shape that the metrics pipeline produces correct Rows.
"""

from datetime import UTC, datetime

from git_dev_metrics.cache import Cache
from git_dev_metrics.metrics.snapshot import MetricsSnapshot
from git_dev_metrics.utils.date_utils import month_range


def _pr(
    number: int,
    login: str,
    merged_day: int,
    additions: int = 100,
    deletions: int = 50,
    changed_files: int = 5,
    reviews: list[dict] | None = None,
    state: str = "merged",
) -> dict:
    return {
        "id": number,
        "number": number,
        "state": state,
        "title": f"PR #{number}",
        "user": {"login": login},
        "created_at": datetime(2026, 4, merged_day, 8, 0, 0, tzinfo=UTC),
        "merged_at": datetime(2026, 4, merged_day, 18, 0, 0, tzinfo=UTC),
        "closed_at": datetime(2026, 4, merged_day, 18, 0, 0, tzinfo=UTC),
        "additions": additions,
        "deletions": deletions,
        "changed_files": changed_files,
        "first_commit_at": datetime(2026, 4, merged_day, 6, 0, 0, tzinfo=UTC),
        "ready_for_review_at": datetime(2026, 4, merged_day, 7, 0, 0, tzinfo=UTC),
        "body": f"Body for #{number}",
        "commit_messages": [f"feat: change for #{number}"],
        "reviews": reviews or [],
    }


def _review(login: str, day: int) -> dict:
    return {
        "user": {"login": login},
        "state": "APPROVED",
        "submitted_at": datetime(2026, 4, day, 12, 0, 0, tzinfo=UTC),
    }


class TestCacheToSnapshotRoundTrip:
    def test_should_compute_row_values_after_cache_round_trip(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        prs_repo1 = [
            _pr(101, "alice", 5, reviews=[_review("bob", 5)]),
            _pr(102, "bob", 12),
        ]
        prs_repo2 = [
            _pr(103, "alice", 20, additions=50, deletions=25, changed_files=3),
        ]

        cache = Cache(db_path)
        cache.store_prs(prs_repo1, "myorg", "repo1", 2026, 4)
        cache.seal_month("myorg", "repo1", 2026, 4)
        cache.store_prs(prs_repo2, "myorg", "repo2", 2026, 4)
        cache.seal_month("myorg", "repo2", 2026, 4)

        # Act
        repo_prs = cache.load_all_repos_for_range([(2026, 4)])
        snapshot = MetricsSnapshot.from_repo_prs(repo_prs, month_range(2026, 4))

        # Assert
        dev_rows = {r.name: r for r in snapshot.devs}
        assert set(dev_rows) == {"alice", "bob"}
        assert dev_rows["alice"].pr_count == 2
        assert dev_rows["alice"].reviews_given == 0
        assert dev_rows["bob"].pr_count == 1
        assert dev_rows["bob"].reviews_given == 1
        assert snapshot.team.pr_count == 3
        assert snapshot.team.reviews_given == 1
        for row in [*snapshot.devs, snapshot.team]:
            assert isinstance(row.health, int)
            assert row.band in ("good", "ok", "bad")

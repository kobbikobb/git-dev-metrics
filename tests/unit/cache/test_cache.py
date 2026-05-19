import json

from git_dev_metrics.cache import (
    count_prs,
    insert_prs,
    is_sealed,
    open_connection,
    query_prs,
    seal_month,
)

from ..conftest import any_pr, approved_review, dt


class TestInsertPrs:
    def test_should_persist_prs_and_reviews(self, tmp_path):
        db_path = tmp_path / "cache.db"
        prs = [
            any_pr(id=1, number=1, user={"login": "dev-a"}, commit_messages=["msg-1"]),
            any_pr(
                id=2,
                number=2,
                user={"login": "dev-b"},
                reviews=[approved_review(login="reviewer-x")],
            ),
        ]

        insert_prs(prs, "myorg", "myrepo", 2026, 4, db_path=db_path)

        rows = query_prs("myorg", "myrepo", 2026, 4, db_path=db_path)
        assert {row["number"] for row in rows} == {1, 2}
        commits = next(row["commit_messages_json"] for row in rows if row["number"] == 1)
        assert json.loads(commits) == ["msg-1"]
        conn = open_connection(db_path)
        reviews = conn.execute("SELECT * FROM reviews").fetchall()
        assert [r["user_login"] for r in reviews] == ["reviewer-x"]

    def test_should_insert_pr_in_real_mapper_shape(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        pr_from_mapper = {
            "number": 42,
            "title": "Real PR",
            "created_at": dt(year=2026, month=4, day=5, hour=8, minute=0),
            "merged_at": dt(year=2026, month=4, day=5, hour=18, minute=0),
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
            "user": {"login": "alice"},
            "first_commit_at": None,
            "ready_for_review_at": None,
            "body": None,
            "commit_messages": ["feat: x"],
            "reviews": [],
        }

        # Act
        insert_prs([pr_from_mapper], "myorg", "myrepo", 2026, 4, db_path=db_path)

        # Assert
        rows = query_prs("myorg", "myrepo", 2026, 4, db_path=db_path)
        assert len(rows) == 1
        assert rows[0]["number"] == 42
        assert rows[0]["author_login"] == "alice"
        assert rows[0]["state"] is None
        assert rows[0]["closed_at"] is None

    def test_should_replace_existing_pr_on_reinsert(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        first = any_pr(number=7, title="first", additions=10)
        second = any_pr(number=7, title="second", additions=99)

        # Act
        insert_prs([first], "myorg", "myrepo", 2026, 4, db_path=db_path)
        insert_prs([second], "myorg", "myrepo", 2026, 4, db_path=db_path)

        # Assert
        rows = query_prs("myorg", "myrepo", 2026, 4, db_path=db_path)
        assert len(rows) == 1
        assert rows[0]["title"] == "second"
        assert rows[0]["additions"] == 99

    def test_should_persist_multiple_reviews_per_pr(self, tmp_path):
        # Arrange
        db_path = tmp_path / "cache.db"
        pr = any_pr(
            number=5,
            reviews=[
                approved_review(
                    login="bob", submitted_at=dt(year=2026, month=4, day=2, hour=10, minute=0)
                ),
                approved_review(
                    login="carol", submitted_at=dt(year=2026, month=4, day=2, hour=11, minute=0)
                ),
            ],
        )

        # Act
        insert_prs([pr], "myorg", "myrepo", 2026, 4, db_path=db_path)

        # Assert
        conn = open_connection(db_path)
        review_rows = conn.execute("SELECT * FROM reviews WHERE pr_number = ?", (5,)).fetchall()
        assert len(review_rows) == 2
        assert {r["user_login"] for r in review_rows} == {"bob", "carol"}


class TestSealing:
    def test_should_record_seal_for_repo_month(self, tmp_path):
        db_path = tmp_path / "cache.db"

        seal_month("myorg", "myrepo", 2026, 4, db_path=db_path)

        assert is_sealed("myorg", "myrepo", 2026, 4, db_path=db_path) is True
        assert is_sealed("myorg", "myrepo", 2026, 5, db_path=db_path) is False

    def test_should_count_prs_for_scope(self, tmp_path):
        db_path = tmp_path / "cache.db"
        insert_prs(
            [any_pr(number=10), any_pr(number=11)],
            "myorg",
            "myrepo",
            2026,
            4,
            db_path=db_path,
        )

        result = count_prs("myorg", "myrepo", 2026, 4, db_path=db_path)

        assert result == 2

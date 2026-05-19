import json

from git_dev_metrics.cache import Cache

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

        cache = Cache(db_path)
        cache.store_prs(prs, "myorg", "myrepo", 2026, 4)

        rows = cache.query_prs("myorg", "myrepo", 2026, 4)
        assert {row["number"] for row in rows} == {1, 2}
        commits = next(row["commit_messages_json"] for row in rows if row["number"] == 1)
        assert json.loads(commits) == ["msg-1"]
        reviews = cache.conn.execute("SELECT * FROM reviews").fetchall()
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
        cache = Cache(db_path)
        cache.store_prs([pr_from_mapper], "myorg", "myrepo", 2026, 4)

        # Assert
        rows = cache.query_prs("myorg", "myrepo", 2026, 4)
        assert len(rows) == 1
        assert rows[0]["number"] == 42
        assert rows[0]["author_login"] == "alice"
        assert rows[0]["state"] is None
        assert rows[0]["closed_at"] is None

    def test_should_replace_existing_pr_on_reinsert(self, tmp_path):
        # Arrange
        cache = Cache(tmp_path / "cache.db")
        first = any_pr(number=7, title="first", additions=10)
        second = any_pr(number=7, title="second", additions=99)

        # Act
        cache.store_prs([first], "myorg", "myrepo", 2026, 4)
        cache.store_prs([second], "myorg", "myrepo", 2026, 4)

        # Assert
        rows = cache.query_prs("myorg", "myrepo", 2026, 4)
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
        cache = Cache(db_path)
        cache.store_prs([pr], "myorg", "myrepo", 2026, 4)

        # Assert
        review_rows = cache.conn.execute("SELECT * FROM reviews WHERE pr_number = ?", (5,)).fetchall()
        assert len(review_rows) == 2
        assert {r["user_login"] for r in review_rows} == {"bob", "carol"}


class TestSealing:
    def test_should_record_seal_for_repo_month(self, tmp_path):
        db_path = tmp_path / "cache.db"

        cache = Cache(db_path)
        cache.seal_month("myorg", "myrepo", 2026, 4)

        assert cache.is_sealed("myorg", "myrepo", 2026, 4) is True
        assert cache.is_sealed("myorg", "myrepo", 2026, 5) is False

    def test_should_count_prs_for_scope(self, tmp_path):
        cache = Cache(tmp_path / "cache.db")
        cache.store_prs(
            [any_pr(number=10), any_pr(number=11)],
            "myorg",
            "myrepo",
            2026,
            4,
        )

        result = cache.count_prs("myorg", "myrepo", 2026, 4)

        assert result == 2

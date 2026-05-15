from git_dev_metrics.cache import insert_prs, load_prs

from ..conftest import any_pr, approved_review, dt


class TestLoadPrs:
    def test_should_round_trip_prs_with_reviews(self, tmp_path):
        db_path = tmp_path / "cache.db"
        prs = [
            any_pr(
                id=1,
                number=11,
                user={"login": "alice"},
                additions=42,
                deletions=7,
                changed_files=3,
                commit_messages=["feat: a", "fix: b"],
                reviews=[
                    approved_review(
                        login="bob", submitted_at=dt(year=2026, month=4, day=2, hour=9, minute=0)
                    )
                ],
            ),
            any_pr(id=2, number=12, user={"login": "carol"}, commit_messages=[], reviews=[]),
        ]
        insert_prs(prs, "myorg", "myrepo", 2026, 4, db_path=db_path)

        loaded = load_prs("myorg", "myrepo", 2026, 4, db_path=db_path)

        by_number = {pr["number"]: pr for pr in loaded}
        assert set(by_number) == {11, 12}
        assert by_number[11]["user"]["login"] == "alice"
        assert by_number[11]["additions"] == 42
        assert by_number[11]["commit_messages"] == ["feat: a", "fix: b"]
        assert len(by_number[11]["reviews"]) == 1
        assert by_number[11]["reviews"][0]["user"]["login"] == "bob"
        assert by_number[11]["reviews"][0]["state"] == "APPROVED"
        assert by_number[12]["reviews"] == []
        assert by_number[12]["commit_messages"] == []

    def test_should_return_empty_list_when_no_rows(self, tmp_path):
        db_path = tmp_path / "cache.db"

        loaded = load_prs("myorg", "myrepo", 2026, 4, db_path=db_path)

        assert loaded == []

    def test_should_scope_reviews_to_matching_month(self, tmp_path):
        db_path = tmp_path / "cache.db"
        april = [any_pr(id=1, number=1, reviews=[approved_review(login="bob")])]
        march = [any_pr(id=99, number=99, reviews=[approved_review(login="ghost")])]
        insert_prs(april, "myorg", "myrepo", 2026, 4, db_path=db_path)
        insert_prs(march, "myorg", "myrepo", 2026, 3, db_path=db_path)

        loaded = load_prs("myorg", "myrepo", 2026, 4, db_path=db_path)

        assert len(loaded) == 1
        assert [r["user"]["login"] for r in loaded[0]["reviews"]] == ["bob"]

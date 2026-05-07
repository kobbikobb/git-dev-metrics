from git_dev_metrics.metrics.anonymize import anonymize_metrics, anonymize_stale_prs


class TestAnonymizeMetrics:
    def test_should_replace_dev_logins_with_pseudonyms(self):
        metrics = {
            "dev_metrics": {"zoe": {"pr_count": 1}, "alice": {"pr_count": 2}},
            "reviewer_counts": {"zoe": 3, "bob": 4},
        }

        result = anonymize_metrics(metrics)

        # mapping is alphabetical by login: alice -> dev-1, bob -> dev-2, zoe -> dev-3
        assert set(result["dev_metrics"].keys()) == {"dev-1", "dev-3"}
        assert set(result["reviewer_counts"].keys()) == {"dev-2", "dev-3"}
        assert result["dev_metrics"]["dev-1"] == {"pr_count": 2}
        assert result["reviewer_counts"]["dev-3"] == 3

    def test_should_preserve_unrelated_keys(self):
        metrics = {
            "dev_metrics": {"alice": {"pr_count": 1}},
            "reviewer_counts": {"alice": 1},
            "team_metrics": {"pr_count": 1},
            "repo_metrics": {"org/repo": {}},
        }

        result = anonymize_metrics(metrics)

        assert result["team_metrics"] == {"pr_count": 1}
        assert result["repo_metrics"] == {"org/repo": {}}

    def test_should_handle_reviewer_only_logins(self):
        metrics = {
            "dev_metrics": {"alice": {"pr_count": 1}},
            "reviewer_counts": {"alice": 1, "bob": 5},
        }

        result = anonymize_metrics(metrics)

        # bob never authored, only reviewed -- still gets a pseudonym
        assert "dev-2" in result["reviewer_counts"]
        assert "dev-2" not in result["dev_metrics"]


class TestAnonymizeStalePrs:
    def test_should_replace_author_via_mapping(self):
        mapping = {"alice": "dev-1", "bob": "dev-2"}
        prs = [
            {"author": "alice", "number": 1, "title": "x"},
            {"author": "bob", "number": 2, "title": "y"},
        ]

        result = anonymize_stale_prs(prs, mapping)

        assert result[0]["author"] == "dev-1"
        assert result[1]["author"] == "dev-2"
        assert result[0]["title"] == "x"

    def test_should_pass_through_unmapped_authors(self):
        prs = [{"author": "ghost", "number": 1, "title": "x"}]

        result = anonymize_stale_prs(prs, {})

        assert result[0]["author"] == "ghost"

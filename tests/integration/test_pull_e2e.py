"""End-to-end tests for the pull command: raw GraphQL → mapper → cache → report.

These exist so a shape change in `map_pull_request` (or anywhere it touches the
cache) breaks a test, not the next live `gdm pull`.
"""

from typer.testing import CliRunner

from git_dev_metrics.cache import count_prs, is_sealed, query_prs
from git_dev_metrics.cli.app import app
from git_dev_metrics.github._response_mapper import map_pull_request

runner = CliRunner()


def _raw_pr(number: int, author: str, merged_day: int, reviews: list[dict] | None = None) -> dict:
    """A raw GraphQL search node for one merged PR, in the shape GitHub returns."""
    return {
        "number": number,
        "title": f"PR #{number}",
        "createdAt": f"2026-04-{merged_day:02d}T08:00:00Z",
        "mergedAt": f"2026-04-{merged_day:02d}T18:00:00Z",
        "additions": 100,
        "deletions": 50,
        "changedFiles": 5,
        "author": {"login": author},
        "body": f"Body for #{number}",
        "commits": {
            "nodes": [
                {
                    "commit": {
                        "committedDate": f"2026-04-{merged_day:02d}T06:00:00Z",
                        "message": f"feat: change for #{number}",
                    }
                }
            ]
        },
        "reviews": {"nodes": reviews or []},
        "timelineItems": {"nodes": []},
    }


def _raw_review(login: str, day: int) -> dict:
    return {
        "author": {"login": login},
        "state": "APPROVED",
        "submittedAt": f"2026-04-{day:02d}T12:00:00Z",
    }


class TestPullEndToEnd:
    def test_should_insert_real_mapper_output_into_cache(self, tmp_path, mocker):
        # Arrange
        db_path = tmp_path / "cache.db"
        raw = [
            _raw_pr(101, "alice", 5, [_raw_review("bob", 5)]),
            _raw_pr(102, "bob", 12, []),
            _raw_pr(103, "alice", 22, [_raw_review("carol", 22), _raw_review("dave", 23)]),
        ]
        mapped = [map_pull_request(pr) for pr in raw]
        mocker.patch(
            "git_dev_metrics.cli.commands.pull.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.runners.pull_runner.fetch_repo_metrics", return_value=mapped
        )

        # Act
        result = runner.invoke(
            app,
            [
                "pull",
                "--month",
                "2026-04",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        assert is_sealed("myorg", "myrepo", 2026, 4, db_path=db_path)
        assert count_prs("myorg", "myrepo", 2026, 4, db_path=db_path) == 3
        rows = query_prs("myorg", "myrepo", 2026, 4, db_path=db_path)
        by_number = {row["number"]: row for row in rows}
        assert set(by_number) == {101, 102, 103}
        assert by_number[101]["author_login"] == "alice"
        assert by_number[103]["author_login"] == "alice"

    def test_should_chain_pull_then_dashboard_then_clear(self, tmp_path, mocker):
        # Arrange
        db_path = tmp_path / "cache.db"
        raw = [
            _raw_pr(201, "alice", 3, [_raw_review("bob", 3)]),
            _raw_pr(202, "bob", 9, [_raw_review("alice", 9)]),
        ]
        mapped = [map_pull_request(pr) for pr in raw]
        mocker.patch(
            "git_dev_metrics.cli.commands.pull.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.runners.pull_runner.fetch_repo_metrics", return_value=mapped
        )
        mocker.patch("webbrowser.open")
        dashboard_out = tmp_path / "r.html"

        # Act
        pull_result = runner.invoke(
            app,
            [
                "pull",
                "--month",
                "2026-04",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
            ],
        )
        dashboard_result = runner.invoke(
            app,
            [
                "dashboard",
                "--from",
                "2026-04",
                "--to",
                "2026-04",
                "--db",
                str(db_path),
                "--output",
                str(dashboard_out),
            ],
        )
        clear_result = runner.invoke(app, ["clear", "--db", str(db_path), "--yes"])

        # Assert
        assert pull_result.exit_code == 0, pull_result.output
        assert dashboard_result.exit_code == 0, dashboard_result.output
        assert dashboard_out.exists()
        html = dashboard_out.read_text().lower()
        assert "<html" in html
        assert "alice" in html
        assert "bob" in html
        assert clear_result.exit_code == 0
        assert not db_path.exists()

    def test_should_handle_pr_with_minimal_fields(self, tmp_path, mocker):
        # Arrange
        db_path = tmp_path / "cache.db"
        # Minimal real-shape PR: no body, no commits, no reviews, unknown author.
        minimal = {
            "number": 999,
            "title": "Minimal",
            "createdAt": "2026-04-15T08:00:00Z",
            "mergedAt": "2026-04-15T18:00:00Z",
            "additions": 0,
            "deletions": 0,
            "changedFiles": 0,
            "author": None,
            "body": None,
            "commits": {"nodes": []},
            "reviews": {"nodes": []},
            "timelineItems": {"nodes": []},
        }
        mapped = [map_pull_request(minimal)]
        mocker.patch(
            "git_dev_metrics.cli.commands.pull.get_github_token", return_value="fake-token"
        )
        mocker.patch(
            "git_dev_metrics.cli.runners.pull_runner.fetch_repo_metrics", return_value=mapped
        )

        # Act
        result = runner.invoke(
            app,
            [
                "pull",
                "--month",
                "2026-04",
                "--org",
                "myorg",
                "--repo",
                "myrepo",
                "--db",
                str(db_path),
            ],
        )

        # Assert
        assert result.exit_code == 0, result.output
        rows = query_prs("myorg", "myrepo", 2026, 4, db_path=db_path)
        assert len(rows) == 1
        assert rows[0]["number"] == 999
        assert rows[0]["author_login"] == "unknown"
        assert rows[0]["body"] is None

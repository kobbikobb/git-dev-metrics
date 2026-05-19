import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from ..models import PullRequest, Review
from ..utils.date_utils import parse_iso_datetime
from .db import open_connection


def _review(row: sqlite3.Row) -> Review:
    return {
        "user": {"login": row["user_login"] or ""},
        "state": row["state"] or "",
        "submitted_at": parse_iso_datetime(row["submitted_at"]),
    }


def _pr(row: sqlite3.Row, reviews: list[Review]) -> PullRequest:
    return {  # type: ignore[return-value]
        "number": row["number"],
        "state": row["state"] or "",
        "title": row["title"] or "",
        "user": {"login": row["author_login"] or ""},
        "created_at": parse_iso_datetime(row["created_at"]),
        "merged_at": parse_iso_datetime(row["merged_at"]),
        "closed_at": parse_iso_datetime(row["closed_at"]),
        "additions": row["additions"] or 0,
        "deletions": row["deletions"] or 0,
        "changed_files": row["changed_files"] or 0,
        "first_commit_at": parse_iso_datetime(row["first_commit_at"]),
        "ready_for_review_at": parse_iso_datetime(row["ready_for_review_at"]),
        "body": row["body"],
        "commit_messages": json.loads(row["commit_messages_json"] or "[]"),
        "reviews": reviews,
    }


def load_prs(
    org: str, repo: str, year: int, month: int, db_path: Path | None = None
) -> list[PullRequest]:
    """Reconstruct cached PRs (with attached reviews) as a list of PullRequest TypedDicts."""
    conn = open_connection(db_path)
    pr_rows = conn.execute(
        "SELECT * FROM prs WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
        (org, repo, year, month),
    ).fetchall()
    review_rows = conn.execute(
        "SELECT * FROM reviews WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
        (org, repo, year, month),
    ).fetchall()

    by_pr: dict[int, list[Review]] = defaultdict(list)
    for row in review_rows:
        by_pr[row["pr_number"]].append(_review(row))

    return [_pr(row, by_pr.get(row["number"], [])) for row in pr_rows]


def load_prs_for_range(
    org: str,
    repo: str,
    months: list[tuple[int, int]],
    db_path: Path | None = None,
) -> dict[tuple[int, int], list[PullRequest]]:
    """Reconstruct cached PRs grouped by (year, month) for each requested month."""
    return {
        (year, month): load_prs(org, repo, year, month, db_path=db_path) for year, month in months
    }


def load_all_repos_for_range(
    months: list[tuple[int, int]],
    db_path: Path | None = None,
) -> dict[str, list[PullRequest]]:
    """All cached PRs per `"org/repo"` for sealed (org, repo, year, month) tuples in the range."""
    wanted = set(months)
    out: dict[str, list[PullRequest]] = {}
    for org, repo, year, month in list_synced_months(db_path=db_path):
        if (year, month) not in wanted:
            continue
        out.setdefault(f"{org}/{repo}", []).extend(
            load_prs(org, repo, year, month, db_path=db_path)
        )
    return out


def load_all_repos_by_month(
    months: list[tuple[int, int]],
    db_path: Path | None = None,
) -> dict[tuple[int, int], list[PullRequest]]:
    """All cached PRs grouped by (year, month), aggregated across every sealed repo."""
    wanted = set(months)
    out: dict[tuple[int, int], list[PullRequest]] = {ym: [] for ym in months}
    for org, repo, year, month in list_synced_months(db_path=db_path):
        if (year, month) not in wanted:
            continue
        out[(year, month)].extend(load_prs(org, repo, year, month, db_path=db_path))
    return out


def list_synced_months(db_path: Path | None = None) -> list[tuple[str, str, int, int]]:
    """All sealed (org, repo, year, month) tuples, newest first."""
    conn = open_connection(db_path)
    rows = conn.execute(
        "SELECT repo_org, repo_name, year, month FROM sealed_months "
        "ORDER BY year DESC, month DESC, repo_org, repo_name"
    ).fetchall()
    return [(row["repo_org"], row["repo_name"], row["year"], row["month"]) for row in rows]

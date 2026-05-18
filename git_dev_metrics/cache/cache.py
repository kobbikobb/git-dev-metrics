import json
import sqlite3
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models import PullRequest, Review
from ..utils.date_utils import parse_iso_datetime

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prs (
    repo_org TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    number INTEGER NOT NULL,
    state TEXT,
    title TEXT,
    author_login TEXT,
    created_at TEXT,
    merged_at TEXT,
    closed_at TEXT,
    additions INTEGER,
    deletions INTEGER,
    changed_files INTEGER,
    first_commit_at TEXT,
    ready_for_review_at TEXT,
    body TEXT,
    commit_messages_json TEXT,
    PRIMARY KEY (repo_org, repo_name, year, month, number)
);

CREATE TABLE IF NOT EXISTS reviews (
    pr_number INTEGER NOT NULL,
    repo_org TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    user_login TEXT,
    state TEXT,
    submitted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_reviews_scope
    ON reviews (repo_org, repo_name, year, month);

CREATE TABLE IF NOT EXISTS sealed_months (
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    repo_org TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    sealed_at TEXT NOT NULL,
    PRIMARY KEY (year, month, repo_org, repo_name)
);
"""


def default_db_path() -> Path:
    return Path.home() / ".gdm" / "cache.db"


class Cache:
    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            path = self._db_path or default_db_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.executescript(_SCHEMA)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── write ────────────────────────────────────────────

    def store_prs(
        self,
        prs: Sequence[Mapping[str, Any]],
        org: str,
        repo: str,
        year: int,
        month: int,
    ) -> None:
        conn = self.conn
        with conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO prs (
                    repo_org, repo_name, year, month, number, state, title,
                    author_login, created_at, merged_at, closed_at,
                    additions, deletions, changed_files,
                    first_commit_at, ready_for_review_at, body, commit_messages_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_pr_row(pr, org, repo, year, month) for pr in prs],
            )
            review_rows = [row for pr in prs for row in _review_rows(pr, org, repo, year, month)]
            if review_rows:
                conn.executemany(
                    """
                    INSERT INTO reviews (
                        pr_number, repo_org, repo_name, year, month,
                        user_login, state, submitted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    review_rows,
                )

    def seal_month(self, org: str, repo: str, year: int, month: int) -> None:
        conn = self.conn
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO sealed_months "
                "(year, month, repo_org, repo_name, sealed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (year, month, org, repo, datetime.now(UTC).isoformat()),
            )

    # ── read ─────────────────────────────────────────────

    def is_sealed(self, org: str, repo: str, year: int, month: int) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sealed_months WHERE year = ? AND month = ? "
            "AND repo_org = ? AND repo_name = ?",
            (year, month, org, repo),
        ).fetchone()
        return row is not None

    def count_prs(self, org: str, repo: str, year: int, month: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM prs "
            "WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
            (org, repo, year, month),
        ).fetchone()
        return row["n"] if row else 0

    def query_prs(self, org: str, repo: str, year: int, month: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM prs WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
            (org, repo, year, month),
        ).fetchall()

    def load_prs(self, org: str, repo: str, year: int, month: int) -> list[PullRequest]:
        pr_rows = self.conn.execute(
            "SELECT * FROM prs WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
            (org, repo, year, month),
        ).fetchall()
        review_rows = self.conn.execute(
            "SELECT * FROM reviews WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
            (org, repo, year, month),
        ).fetchall()

        by_pr: dict[int, list[Review]] = defaultdict(list)
        for review_row in review_rows:
            by_pr[review_row["pr_number"]].append(_review(review_row))

        return [_pr(pr_row, by_pr.get(pr_row["number"], [])) for pr_row in pr_rows]

    def load_prs_for_range(
        self,
        org: str,
        repo: str,
        months: list[tuple[int, int]],
    ) -> dict[tuple[int, int], list[PullRequest]]:
        return {(year, month): self.load_prs(org, repo, year, month) for year, month in months}

    def load_all_repos_for_range(
        self,
        months: list[tuple[int, int]],
    ) -> dict[str, list[PullRequest]]:
        wanted = set(months)
        out: dict[str, list[PullRequest]] = {}
        for org, repo, year, month in self.list_synced_months():
            if (year, month) not in wanted:
                continue
            out.setdefault(f"{org}/{repo}", []).extend(self.load_prs(org, repo, year, month))
        return out

    def load_all_repos_by_month(
        self,
        months: list[tuple[int, int]],
    ) -> dict[tuple[int, int], list[PullRequest]]:
        wanted = set(months)
        out: dict[tuple[int, int], list[PullRequest]] = {ym: [] for ym in months}
        for org, repo, year, month in self.list_synced_months():
            if (year, month) not in wanted:
                continue
            out[(year, month)].extend(self.load_prs(org, repo, year, month))
        return out

    def list_synced_months(self) -> list[tuple[str, str, int, int]]:
        rows = self.conn.execute(
            "SELECT repo_org, repo_name, year, month FROM sealed_months "
            "ORDER BY year DESC, month DESC, repo_org, repo_name"
        ).fetchall()
        return [(row["repo_org"], row["repo_name"], row["year"], row["month"]) for row in rows]

    @property
    def db_path(self) -> Path:
        """Resolved database path (useful for deletion etc.)."""
        return self._db_path or default_db_path()


# ── private helpers ────────────────────────────────────


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _pr_row(pr: Mapping[str, Any], org: str, repo: str, year: int, month: int) -> tuple:
    return (
        org,
        repo,
        year,
        month,
        pr.get("number"),
        pr.get("state"),
        pr.get("title"),
        (pr.get("user") or {}).get("login"),
        _iso(pr.get("created_at")),
        _iso(pr.get("merged_at")),
        _iso(pr.get("closed_at")),
        pr.get("additions"),
        pr.get("deletions"),
        pr.get("changed_files"),
        _iso(pr.get("first_commit_at")),
        _iso(pr.get("ready_for_review_at")),
        pr.get("body"),
        json.dumps(pr.get("commit_messages") or []),
    )


def _review_rows(pr: Mapping[str, Any], org: str, repo: str, year: int, month: int) -> list[tuple]:
    rows = []
    for review in pr.get("reviews") or []:
        rows.append(
            (
                pr.get("number"),
                org,
                repo,
                year,
                month,
                (review.get("user") or {}).get("login"),
                review.get("state"),
                _iso(review.get("submitted_at")),
            )
        )
    return rows


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

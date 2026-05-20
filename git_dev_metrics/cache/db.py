import json
import sqlite3
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_connections: dict[Path, sqlite3.Connection] = {}

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


def open_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or default_db_path()
    if path in _connections:
        return _connections[path]
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(_SCHEMA)
    _connections[path] = conn
    return conn


def close_connection(db_path: Path | None = None) -> None:
    path = db_path or default_db_path()
    conn = _connections.pop(path, None)
    if conn is not None:
        conn.close()


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
    return [
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
        for review in pr.get("reviews") or []
    ]


def insert_prs(
    prs: Sequence[Mapping[str, Any]],
    org: str,
    repo: str,
    year: int,
    month: int,
    db_path: Path | None = None,
) -> None:
    conn = open_connection(db_path)
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


def seal_month(
    org: str,
    repo: str,
    year: int,
    month: int,
    db_path: Path | None = None,
) -> None:
    conn = open_connection(db_path)
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO sealed_months (year, month, repo_org, repo_name, sealed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (year, month, org, repo, datetime.now(UTC).isoformat()),
        )


def is_sealed(
    org: str,
    repo: str,
    year: int,
    month: int,
    db_path: Path | None = None,
) -> bool:
    conn = open_connection(db_path)
    row = conn.execute(
        "SELECT 1 FROM sealed_months WHERE year = ? AND month = ? "
        "AND repo_org = ? AND repo_name = ?",
        (year, month, org, repo),
    ).fetchone()
    return row is not None


def query_prs(
    org: str,
    repo: str,
    year: int,
    month: int,
    db_path: Path | None = None,
) -> list[sqlite3.Row]:
    conn = open_connection(db_path)
    return conn.execute(
        "SELECT * FROM prs WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
        (org, repo, year, month),
    ).fetchall()


def count_prs(
    org: str,
    repo: str,
    year: int,
    month: int,
    db_path: Path | None = None,
) -> int:
    conn = open_connection(db_path)
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM prs "
        "WHERE repo_org = ? AND repo_name = ? AND year = ? AND month = ?",
        (org, repo, year, month),
    ).fetchone()
    return row["n"] if row else 0

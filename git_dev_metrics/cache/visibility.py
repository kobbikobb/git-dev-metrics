from pathlib import Path

from .db import open_connection


def get_hidden_logins(db_path: Path | None = None) -> set[str]:
    """Return normalized logins hidden from individual report results."""
    conn = open_connection(db_path)
    return {row["login"] for row in conn.execute("SELECT login FROM hidden_logins")}


def update_hidden_logins(changes: dict[str, bool], db_path: Path | None = None) -> None:
    """Apply only the visibility changes made during this session."""
    conn = open_connection(db_path)
    with conn:
        for login, hidden in changes.items():
            if hidden:
                conn.execute("INSERT OR IGNORE INTO hidden_logins VALUES (?)", (login.lower(),))
            else:
                conn.execute("DELETE FROM hidden_logins WHERE login = ?", (login,))

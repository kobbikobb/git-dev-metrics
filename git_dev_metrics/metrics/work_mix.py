"""Monthly work-category counts for synced repositories."""

from collections import Counter
from pathlib import Path
from typing import TypedDict

from ..cache import open_connection


class MonthMix(TypedDict):
    partial: bool
    counts: dict[str, int]


def monthly_work_mix(start: str, end: str, db: Path | None) -> dict[str, dict[str, MonthMix]]:
    conn = open_connection(db)
    repos: dict[str, dict[str, MonthMix]] = {
        name: {}
        for (name,) in conn.execute(
            "SELECT DISTINCT lower(repo_org || '/' || repo_name) FROM synced_months"
        )
    }
    rows = conn.execute(
        """WITH coverage AS (
               SELECT lower(repo_org) AS org, lower(repo_name) AS repo,
                      printf('%04d-%02d', year, month) AS month, min(partial) AS partial
               FROM synced_months GROUP BY 1, 2, 3
           ), merges AS (
               SELECT DISTINCT lower(repo_org) AS org, lower(repo_name) AS repo,
                      strftime('%Y-%m', merged_at) AS month, number
               FROM prs WHERE strftime('%Y-%m', merged_at) BETWEEN ? AND ?
           )
           SELECT s.org || '/' || s.repo AS repository, s.month, s.partial,
                  coalesce(c.category, 'unclassified') AS category, count(m.number) AS n
           FROM coverage s LEFT JOIN merges m USING (org, repo, month)
           LEFT JOIN pr_classifications c ON c.repo_org = m.org AND c.repo_name = m.repo
               AND c.number = m.number
           WHERE s.month BETWEEN ? AND ?
           GROUP BY s.org, s.repo, s.month, category ORDER BY repository, s.month""",
        (start, end, start, end),
    )
    for repo, month, partial, category, count in rows:
        data = repos.setdefault(repo, {}).setdefault(
            month, MonthMix(partial=bool(partial), counts={})
        )
        if count:
            data["counts"][category] = count
    return repos


def combined_work_mix(
    repos: dict[str, dict[str, MonthMix]], months: list[str]
) -> dict[str, MonthMix]:
    combined = {}
    for month in months:
        rows = [data[month] for data in repos.values() if month in data]
        if rows:
            counts: Counter[str] = Counter()
            for row in rows:
                counts.update(row["counts"])
            combined[month] = MonthMix(
                partial=len(rows) < len(repos) or any(row["partial"] for row in rows),
                counts=dict(counts),
            )
    return combined

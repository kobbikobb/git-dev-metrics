# SQLite for metric storage

## Problem

Needed a local store for sealed PR data that requires zero setup and ships with the language.

## Options

Postgres, Parquet files, or another store (deferred — can evaluate when the project outgrows SQLite). SQLite (chosen).

## Solution

SQLite with three tables (`prs`, `reviews`, `sealed_months`), accessed via raw SQL with `executemany`. No ORM. The schema is deliberately flat — it mirrors the GitHub API response shape.

## Consequences

Schema is tightly coupled to GitHub's response shape. If we later need a different query pattern (e.g., cross-repo analytics), migration to another store is possible without changing the cache-layer interface.

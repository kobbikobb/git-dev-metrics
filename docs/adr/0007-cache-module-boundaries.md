# Cache module boundaries

## Problem

The cache layer had 3 files: `db.py` (schema + write operations), `query.py` (read operations reconstructing typed models), and `__init__.py` (public re-exports). `db.py` opened a fresh SQLite connection per call (221 lines, 7 open/close pairs). `query.py` depended on `db.open_connection` (115 lines, 5 open/close pairs). Both were shallow: every caller opened, operated, and closed a connection. The split between writes and reads didn't match any consumer boundary — callers always used both sides via the `cache` package.

## Options

**Option A — keep 3 files.** Each has a clear concern: persistence vs. query. If a future need requires reading without writing or writing without reading, the split pays off.

Rejected. Every consumer imports from the `cache` package, not from individual files. There is no scenario where a caller needs `db.py` without `query.py` or vice versa. The split adds indirection without abstraction — it's two shallow modules, not two independent concerns.

**Option B — merge into single `Cache` class.** One class owns one lazy connection. All methods (read + write) live on the class. The caller instantiates once, calls freely, and closes explicitly when done. Chosen.

## Solution

Create `cache/cache.py` with `Cache` class. Move all functionality from `db.py` (schema, `store_prs`, `seal_month`, `is_sealed`, `count_prs`, `query_prs`) and `query.py` (`load_prs`, `load_prs_for_range`, `load_all_repos_for_range`, `load_all_repos_by_month`, `list_synced_months`) into the class. `default_db_path()` stays as a standalone function (path builder, not cache logic).

Update `__init__.py` to export `Cache` and `default_db_path`. Update all 7 production callers (`loader.py`, CLI commands, wizards, runners). Rewrite 10 test files to use `Cache`. Delete `db.py` and `query.py`.

## Consequences

- API surface shrinks from 2 modules (10 public functions) to 1 class (11 methods) + 1 standalone function.
- Open-connections-per-call eliminated — one connection per `Cache` instance, lazy-init.
- All callers use the same pattern: `Cache(db_path).method(...)`.
- Test setup simplified: seed via `Cache(db_path).store_prs(...)` and `Cache(db_path).seal_month(...)`.

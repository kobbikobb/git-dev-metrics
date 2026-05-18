# Metric pipeline module boundaries

## Problem

The metric computation pipeline (`metrics/`) had 7 modules that together turned PR data into scored, ranked rows. Three of them were shallow pass-throughs — interfaces nearly as complex as their implementations — serving one consumer (`snapshot.py`). An architecture review flagged them for consolidation. The question was: which modules earn their keep?

## Options

**Option A — keep all 7.** Each file is testable in isolation. The pipeline has clear conceptual stages: raw computation → typed wrapper → per-entity grouping → health scoring → row construction → orchestration.

Rejected. Three files are so thin they add indirection without abstraction. The "stages" are an illusion — `compute_raw` immediately pipes into `compute_dev_metrics` which immediately pipes into `MetricsSnapshot`. Tests for individual stages duplicate the integration tests in `test_snapshot.py`.

**Option B — merge `_raw_metrics`, `_dev_repo_metrics`, and `_row_factory` into `snapshot.py`.** The public interface stays `MetricsSnapshot.from_repo_prs()`. `calculator.py`, `health.py`, `_ai_detection.py`, and `_rows.py` remain separate. Chosen.

**Option C — merge everything including `calculator.py` and `health.py`.** Rejected because:
- `calculator.py` is reused by `trend_calculator.py` (passes the deletion test).
- `health.py` contains 114 lines of genuine domain complexity (weighted formulas, scoring curves, citizenship normalization). Keeping it isolated aids readability.
- `_ai_detection.py` is reused by both snapshot and trend pipelines.
- `_rows.py` is a leaf module with zero internal dependencies — the natural home for shared type definitions.
- `RawMetrics` cannot move into `snapshot.py` (circular dependency: `health.py` → `RawMetrics` ← `snapshot.py` → `health.py`). It was moved into `_rows.py` alongside `Row` and `Summary`.

## Solution

Delete `_raw_metrics.py`, `_dev_repo_metrics.py`, `_row_factory.py`. Their content — `RawMetrics`, `compute_raw`, `compute_dev_metrics`, `compute_repo_metrics`, `band_from_health`, `raw_to_row`, `rank_rows` — was relocated:

| Symbol | Destination |
|--------|-------------|
| `RawMetrics` dataclass | `_rows.py` (leaf module, no deps) |
| `compute_raw`, `compute_dev_metrics`, `compute_repo_metrics`, `raw_to_row`, `rank_rows` | `snapshot.py` (private) |
| `band_from_health` | `snapshot.py` (public — still exported via `__init__`) |

All 5 files that imported from the deleted modules were updated (health.py, __init__.py, test_health.py, test_snapshot.py). Two test files (`test_dev_repo_metrics.py`, `test_row_factory.py`) were deleted — the behaviour they covered (field mapping, sorting, wiring) is exercised by existing `test_snapshot.py` integration tests.

## Consequences

- `metrics/` goes from 14 files to 11 files (including printer/).
- The public API surface shrinks by 3 modules (fewer public import paths).
- `health.py` still imports `RawMetrics` from `_rows.py` — no circular dependency.
- Future metric additions touch at most 3 files: `_rows.py` (new fields), `snapshot.py` (computation), `health.py` (scoring). Previously they might touch 6.
- Test maintainers have fewer files to navigate: 3 test files deleted or merged into `test_snapshot.py`.

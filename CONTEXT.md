# Domain glossary

Vocabulary used across the codebase. Use these terms exactly. If a new concept needs a name, add it here.

## Core objects

- **PR** — a GitHub pull request, hydrated with reviews. Shape: `models.PullRequest` TypedDict (number, state, author, timestamps, additions/deletions, commits, reviews).
- **Repo** — `org/name` pair on GitHub. Always referenced as `"org/repo"` in strings.
- **Dev** — a GitHub login authoring or reviewing PRs. Bots filtered via `constants.is_bot_login`.
- **Period** — closed time window `[since, until)` for one analysis run. Type: `utils.TimePeriod`.
- **Month** — `(year, month)` tuple. The cache seals data at month granularity.
- **Sealed month** — a `(org, repo, year, month)` that has been pulled into the cache and marked complete. Once sealed, contents are immutable.

## Metrics

- **Cycle time** — hours from first commit to merge. See `metrics.calculator.calculate_cycle_time`.
- **Pickup time** — hours from PR ready-for-review to first reviewer action.
- **Review time** — hours of active review.
- **PR size** — lines changed (additions + deletions).
- **Throughput** — total PRs in period.
- **PRs/week** — throughput normalised by period length.
- **Reviews given** — count of reviews a dev submitted on others' PRs.
- **AI percentage** — share of PRs flagged as AI-assisted (heuristic on commit messages / body).

## Aggregation

- **Snapshot** — a `MetricsSnapshot`: a frozen, fully-computed analysis of one period across one or more repos. Owns team, dev, repo rows + summary + reviewer counts. Built once via `MetricsSnapshot.from_repo_prs(repo_prs, period)`. Printers consume snapshots; they do not recompute.
- **Row** — one row of metrics (`Row` dataclass): all per-entity numbers (cycle, pickup, …) plus `health` and `band`. Used for team, dev, repo with the same shape.
- **Summary** — typed cross-format aggregate exposed by the snapshot for the dashboard header (team health, totals, top reviewer, AI distribution).
- **Trend** — a sequence of per-month aggregates across the same scope. Distinct from snapshot: trend is many months × few metrics; snapshot is one period × full breadth. Lives in `metrics.trend_calculator`.
- **Stale PR** — open PR older than the staleness threshold (currently 7 days, `constants`). Lives outside snapshot.

## Health

- **Health score** — 0–100 composite. Two formulas:
  - **Team health**: throughput + speed + pickup + citizenship. Used for team and repo rows.
  - **Dev health**: throughput + speed + citizenship (no pickup — reviewer responsiveness isn't an authoring property).
- **Band** — bucket a health score falls into: `good` (≥80), `ok` (≥60), `bad` (<60). Computed once on the row. Printers map band → emoji or band → colour; they never read the raw thresholds.
- **Citizenship cohort** — when computing dev citizenship, the absolute-review-count component is normalised against the rest of the cohort. The snapshot passes the cohort through internally; callers never have to remember.

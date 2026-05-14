# Snapshot and cache by month

## Problem

Every report re-queried the GitHub API for the same PR data. Building older reports re-fetched months that hadn't changed since the last run.

## Options

Computing metrics on every read (rejected — wasteful for sealed periods, couples reports to API availability). Fetch-once, cache-and-seal (chosen).

## Solution

Pull each month's PRs once and seal them in local storage as an immutable snapshot. The `MetricsSnapshot` is computed upfront from cached PRs and is itself frozen. Callers never re-fetch or recompute for sealed months.

## Consequences

The current month is deferred until it's complete — we never fetch a partial month. Future work could track which days within a month have been fetched for incremental pulls.

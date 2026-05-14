# Fetch once, snapshot and cache by month

We were fetching the same PR data repeatedly — every report re-queried the GitHub API. Since PR data for a closed month is immutable, we decided to pull each month once and seal it in a local cache. The `MetricsSnapshot` is computed upfront from cached PRs and is itself frozen. Callers never re-fetch or recompute.

We intentionally deferred handling partial-month data: the current month is not fetched until it's complete. A future enhancement could track which days within a month have been fetched.

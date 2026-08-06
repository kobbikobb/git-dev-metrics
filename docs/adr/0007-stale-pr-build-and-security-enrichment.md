# Enrich stale PRs with build status and vulnerability severity

## Problem

The stale PR report lists open PRs older than 7 days, but only shows draft/approved flags and labels. Operators cannot tell from the report whether a stale PR is broken (CI red) or fixes a known vulnerability (and how severe). Both signals drive triage priority and were missing.

## Options

- **A · CI badge, security by heuristics** — `statusCheckRollup` for build status; flag security by author/label/title matching. Rejected: no real severity level (critical/high/medium/low), heuristic false positives.
- **B · CI badge + severity via Dependabot alerts REST** — build status from `statusCheckRollup`; join open Dependabot alerts to PRs by `dependabot_update.pull_request_number`, severity from `security_advisory.severity`. Chosen.
- **C · All-GraphQL** — same join via `repository.vulnerabilityAlerts`. Rejected: heavier per-repo query, `dependabotUpdate` link field can be null, filtering all alerts in code.
- **D · Separate security report** — deferred; the stale report is the surface the user asked to enrich.

## Solution

Add `statusCheckRollup { state }` to `OPEN_PRS_QUERY` for a build-status badge. Fetch `GET /repos/{org}/{repo}/dependabot/alerts?state=open` per synced repo via a small REST client, join open alerts to open PRs by `dependabot_update.pull_request_number`, and render the advisory severity (critical/high/medium/low) plus GHSA/CVE id as a badge.

This is a narrow, deliberate exception to ADR-0003 (GraphQL over REST): the authoritative severity data lives on the Dependabot alerts REST endpoint, the GraphQL alternative has an unreliable link field, and it is a single request per repo — not an N+1 pattern.

## Consequences

- New small REST client in the `github` module (first REST surface since ADR-0003). Keep it scoped to dependabot alerts; do not migrate other fetches.
- Token must have repo scope plus security-alert read access; report should degrade gracefully when alerts are unreadable (skip severity, warn).
- Dependabot alerts endpoint is public preview — pin assumptions and tolerate field drift.
- Severity covers only Dependabot/SCA vulnerabilities; code-level (SAST) vulnerabilities stay invisible.
- `statusCheckRollup` is null when a repo has no checks — render "no checks".
- Alerts are paginated; `dependabot_update` is present only on open alerts with an auto-created PR.

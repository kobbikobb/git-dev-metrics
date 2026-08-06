# Enrich stale PRs with build status and vulnerability severity

## Problem

The stale PR report lists open PRs older than 7 days, but only shows draft/approved flags and labels. Operators cannot tell from the report whether a stale PR is broken (CI red) or fixes a known vulnerability (and how severe). Both signals drive triage priority and were missing.

## Options

- **A · CI badge, security by heuristics** — build status from checks; flag security by author/label/title matching. Rejected: no real severity level (critical/high/medium/low), heuristic false positives.
- **B · CI badge + severity via Dependabot alerts REST** — build status from Actions workflow runs; join open Dependabot alerts to PRs by `dependabot_update.pull_request_number`, severity from `security_advisory.severity`. Chosen.
- **C · All-GraphQL** — build status via `statusCheckRollup`; same join via `repository.vulnerabilityAlerts`. Rejected: `statusCheckRollup` needs the Checks permission which fine-grained tokens cannot be granted; `dependabotUpdate` link field can be null, filtering all alerts in code.
- **D · Separate security report** — deferred; the stale report is the surface the user asked to enrich.

## Solution

Read CI build status from `GET /repos/{org}/{repo}/actions/runs?head_sha=...` per open PR head SHA via a small REST client, mapping workflow-run status/conclusion to SUCCESS/FAILURE/PENDING. Fetch `GET /repos/{org}/{repo}/dependabot/alerts?state=open` per synced repo via another small REST client, join open alerts to open PRs by `dependabot_update.pull_request_number`, and render the advisory severity (critical/high/medium/low) plus GHSA/CVE id as a badge.

This is a narrow, deliberate exception to ADR-0003 (GraphQL over REST): both data sources only exist on REST endpoints, the GraphQL alternatives are unreliable or unreadable with fine-grained tokens, and they are bounded requests per repo (build status is one call per head SHA, not a list-all).

## Consequences

- Token must be a fine-grained PAT (classic PATs are rejected at login) with **Actions: Read** and **Dependabot alerts: Read**. Report degrades gracefully when either is missing (skip badge, warn once).
- Fine-grained PATs cannot be granted the Checks permission, so GraphQL `statusCheckRollup` is unusable — build status comes from Actions workflow runs instead. Non-Actions CI shows "no checks".
- New small REST clients in the `github` module (first REST surface since ADR-0003). Keep them scoped to workflow runs and dependabot alerts; do not migrate other fetches.
- Dependabot alerts endpoint is public preview — pin assumptions and tolerate field drift.
- Severity covers only Dependabot/SCA vulnerabilities; code-level (SAST) vulnerabilities stay invisible.
- Alerts are paginated; `dependabot_update` is present only on open alerts with an auto-created PR. A repo with no open Dependabot-update PRs legitimately shows no security values.

# Developer visibility in reports

## Problem

Reports need a way to hide selected developers while continuing to ingest their PRs and reviews.

## Solution

Treat visibility as a local report preference keyed by GitHub login, alongside nicknames. Apply it when selecting individual rows and named highlights. Aggregate metrics use the full activity so a change in visibility preserves historical comparisons.

## Consequences

A hidden developer’s first review still counts toward pickup time. Visible rows can sum to less than the team total. Showing a developer again restores their historical results on the next report run.

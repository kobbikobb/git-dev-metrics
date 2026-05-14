# GraphQL over REST for GitHub data

## Problem

REST required N+1 requests per PR (one for the PR, one for reviews, one for commits). This made bulk historical analysis across many repos prohibitively slow.

## Options

REST (rejected — too chatty for batch analysis). GraphQL (chosen — fetches PRs, reviews, and commits in a single round-trip per page).

## Solution

Use GitHub's GraphQL API (v4). The `graphql_client` module abstracts pagination, retry, and error handling behind a small interface.

## Consequences

Tighter coupling to GitHub's GraphQL schema. More complex query construction. The performance gain (fewer requests, less data) is worth it for the batch-analysis use case.

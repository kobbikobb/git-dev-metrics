# GraphQL over REST for GitHub data

We use GitHub's GraphQL API (v4) instead of REST (v3). GraphQL lets us fetch PRs, reviews, commits, and repo metadata in a single round-trip per page, which is critical for bulk-historically analysis across many repos. REST would require N+1 requests per PR to gather reviews and commits.

The trade-off is more complex query construction and a tight coupling to GitHub's GraphQL schema, but the performance gain (fewer requests, less data transferred) is worth it for the batch-analysis use case.

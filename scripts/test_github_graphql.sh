#!/bin/bash
# Test GitHub GraphQL API endpoint with curl

set -e

OWNER="${1:-octocat}"
REPO="${2:-Hello-World}"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable not set"
    echo "Usage: GITHUB_TOKEN=your_token ./test_github_graphql.sh [owner] [repo]"
    exit 1
fi

QUERY=$(cat << 'EOF'
{
  "query": "query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) { pullRequests(states: MERGED, first: 5, orderBy: {field: MERGED_AT, direction: DESC}) { nodes { number title createdAt mergedAt additions deletions changedFiles author { login } } } } }",
  "variables": {
    "owner": "OWNER_PLACEHOLDER",
    "name": "REPO_PLACEHOLDER"
  }
}
EOF
)

QUERY="${QUERY//OWNER_PLACEHOLDER/$OWNER}"
QUERY="${QUERY//REPO_PLACEHOLDER/$REPO}"

echo "Fetching merged PRs from $OWNER/$REPO..."
echo ""

curl -s -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d "$QUERY" \
  https://api.github.com/graphql | jq .

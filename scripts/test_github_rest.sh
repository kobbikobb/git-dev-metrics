#!/bin/bash
# Test GitHub REST API - list repositories

set -e

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable not set"
    echo "Usage: GITHUB_TOKEN=your_token ./test_github_rest.sh"
    exit 1
fi

echo "Fetching repositories..."
echo ""

curl -s -X GET \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/user/repos?visibility=all&sort=updated&per_page=5" | jq .

from datetime import datetime, timezone, timedelta
from typing import List
from github import Github, Auth, GithubException
from .types import Repository, PullRequest, GitHubAPIError, GitHubNotFoundError
from .auth.github_auth import get_github_token

if __name__ == "__main__":
    token = get_github_token()

    org = "facebook"
    repo = "react"

    since = datetime.now(timezone.utc) - timedelta(days=30)  # Last 30 days

    auth = Auth.Token(token)
    g = Github(auth=auth)

    repository = g.get_repo(f"{org}/{repo}")
    query = f"repo:{org}/{repo} is:pr is:merged merged:>={since.strftime('%Y-%m-%d')}"
    issues = g.search_issues(query, sort="updated", order="desc")

    print(f"Found {issues.totalCount} merged PRs since {since.isoformat()}")
    result = []
    for issue in issues:
        pr_data = {
            "number": issue.number,
            "title": issue.title,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "merged_at": issue.pull_request.merged_at.isoformat()
            if issue.pull_request
            else None,
            "user": {"login": issue.user.login if issue.user else "unknown"},
        }
        result.append(pr_data)
        # pr = issue.as_pull_request()
        # print(f"Processing PR #{pr.number} - {pr.title}")
        # result.append({
        #     "number": pr.number,
        #     "title": pr.title,
        #     "created_at": pr.created_at.isoformat() if pr.created_at else None,
        #     "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
        #     "additions": pr.additions,
        #     "deletions": pr.deletions,
        #     "changed_files": pr.changed_files,
        #     "user": {"login": pr.user.login if pr.user else "unknown"},
        # })
        #

    print(result)

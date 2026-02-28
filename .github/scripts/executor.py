import os
from github import Github

# Use the token passed from the workflow env
gh_token = os.getenv("GITHUB_TOKEN")
gh = Github(gh_token)
repo = gh.get_repo(os.getenv("GITHUB_REPOSITORY"))

# ... rest of your logic (Gemini call, git apply, etc.) ...

# Creating the PR now works because of the permissions block in the YAML
pr = repo.create_pull(
    title=f"AI Fix: {os.getenv('ISSUE_TITLE')}",
    body=f"Closes #{os.getenv('ISSUE_NUMBER')}",
    head=branch_name,
    base="main"
)

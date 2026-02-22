from datetime import datetime
from typing import TypedDict


class Repository(TypedDict):
    full_name: str
    private: bool
    last_pushed: datetime | None


class GitHubUser(TypedDict):
    login: str


class PullRequestInfo(TypedDict):
    created_at: str
    merged_at: str


class PullRequest(PullRequestInfo):
    id: int
    number: int
    state: str
    title: str
    user: GitHubUser
    closed_at: str
    additions: int
    deletions: int
    changed_files: int

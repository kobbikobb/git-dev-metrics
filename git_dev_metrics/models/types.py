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
    first_commit_at: datetime | None


class Review(TypedDict):
    user: GitHubUser
    state: str
    submitted_at: str


class OpenPullRequest(TypedDict):
    number: int
    title: str
    created_at: str | None
    merged_at: str | None
    user: GitHubUser
    is_draft: bool
    is_approved: bool

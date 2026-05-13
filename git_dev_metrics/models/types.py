from datetime import datetime
from typing import TypedDict


class Repository(TypedDict):
    full_name: str
    private: bool
    last_pushed: datetime | None


class GitHubUser(TypedDict):
    login: str


class PullRequestInfo(TypedDict):
    created_at: datetime | None
    merged_at: datetime | None


class Review(TypedDict):
    user: GitHubUser
    state: str
    submitted_at: datetime | None


class PullRequest(PullRequestInfo):
    id: int
    number: int
    state: str
    title: str
    user: GitHubUser
    closed_at: datetime | None
    additions: int
    deletions: int
    changed_files: int
    first_commit_at: datetime | None
    ready_for_review_at: datetime | None
    body: str | None
    commit_messages: list[str]
    reviews: list[Review]


class OpenPullRequest(TypedDict):
    number: int
    title: str
    created_at: datetime | None
    merged_at: datetime | None
    user: GitHubUser
    is_draft: bool
    is_approved: bool

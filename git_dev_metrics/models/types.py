from typing import TypedDict


class RepositoryPermissions(TypedDict):
    admin: bool
    push: bool
    pull: bool


class Repository(TypedDict):
    full_name: str
    private: bool
    permissions: RepositoryPermissions


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

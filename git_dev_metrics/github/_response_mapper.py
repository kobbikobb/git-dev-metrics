from datetime import datetime
from typing import cast

from ..models import PullRequest, Repository, Review
from ..utils.date_utils import parse_iso_datetime


def map_author_login(author: dict | None) -> str:
    """Extract login from author dict, defaulting to 'unknown'."""
    return (author or {}).get("login") or "unknown"


def map_repository(repo: dict) -> Repository:
    """Map GraphQL repository response to internal model."""
    return cast(
        Repository,
        {
            "full_name": repo.get("nameWithOwner") or "",
            "private": repo.get("isPrivate", False),
            "last_pushed": parse_iso_datetime(repo.get("pushedAt")),
        },
    )


def _extract_commit_info(pr: dict) -> tuple[datetime | None, list[str]]:
    commits = pr.get("commits", {}).get("nodes", [])
    first_commit_date = None
    if commits:
        commit_data = commits[-1].get("commit", {})
        committed_at = commit_data.get("committedDate")
        first_commit_date = parse_iso_datetime(committed_at)
    commit_messages = [msg for c in commits if (msg := (c.get("commit") or {}).get("message"))]
    return first_commit_date, commit_messages


def _extract_ready_for_review(pr: dict) -> datetime | None:
    timeline_nodes = (pr.get("timelineItems") or {}).get("nodes") or []
    return next(
        (parse_iso_datetime(n.get("createdAt")) for n in timeline_nodes if n.get("createdAt")),
        None,
    )


def map_pull_request(pr: dict) -> PullRequest:
    """Map GraphQL PR response to internal model."""
    first_commit_date, commit_messages = _extract_commit_info(pr)
    ready_for_review = _extract_ready_for_review(pr)

    return cast(
        PullRequest,
        {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "created_at": parse_iso_datetime(pr.get("createdAt")),
            "merged_at": parse_iso_datetime(pr.get("mergedAt")),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changedFiles", 0),
            "user": {"login": map_author_login(pr.get("author"))},
            "first_commit_at": first_commit_date,
            "ready_for_review_at": ready_for_review,
            "body": pr.get("body"),
            "commit_messages": commit_messages,
            "reviews": [],
        },
    )


def map_review(review: dict) -> Review:
    """Map GraphQL review response to internal model."""
    return cast(
        Review,
        {
            "user": {"login": map_author_login(review.get("author"))},
            "state": review.get("state") or "",
            "submitted_at": parse_iso_datetime(review.get("submittedAt")),
        },
    )

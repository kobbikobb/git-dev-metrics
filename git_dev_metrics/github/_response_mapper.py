from ..models import PullRequest, Repository, Review
from ..utils.date_utils import parse_iso_datetime


def map_author_login(author: dict | None) -> str:
    """Extract login from author dict, defaulting to 'unknown'."""
    return (author or {}).get("login") or "unknown"


def map_repository(repo: dict) -> Repository:
    """Map GraphQL repository response to internal model."""
    return {
        "full_name": repo.get("nameWithOwner"),  # type: ignore[return-value]
        "private": repo.get("isPrivate", False),
        "last_pushed": parse_iso_datetime(repo.get("pushedAt")),
    }


def map_pull_request(pr: dict) -> PullRequest:
    """Map GraphQL PR response to internal model."""
    commits = pr.get("commits", {}).get("nodes", [])
    first_commit_date = None
    if commits:
        commit_data = commits[-1].get("commit", {})
        committed_at = commit_data.get("committedDate")
        first_commit_date = parse_iso_datetime(committed_at)

    commit_messages = [msg for c in commits if (msg := (c.get("commit") or {}).get("message"))]

    timeline_nodes = (pr.get("timelineItems") or {}).get("nodes") or []
    ready_for_review = next(
        (parse_iso_datetime(n.get("createdAt")) for n in timeline_nodes if n.get("createdAt")),
        None,
    )

    return {  # type: ignore[return-value]
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
    }


def map_review(review: dict) -> Review:
    """Map GraphQL review response to internal model."""
    return {
        "user": {"login": map_author_login(review.get("author"))},
        "state": review.get("state"),  # type: ignore[return-value]
        "submitted_at": parse_iso_datetime(review.get("submittedAt")),
    }

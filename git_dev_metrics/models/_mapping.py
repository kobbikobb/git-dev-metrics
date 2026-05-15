from collections.abc import Mapping
from typing import Any

from ..utils.date_utils import parse_iso_datetime
from .types import PullRequest, Review


def pull_request_from_dict(data: Mapping[str, Any], reviews: list[Review]) -> PullRequest:
    return {
        "id": data.get("id") or 0,
        "number": data.get("number", 0) or 0,
        "state": data.get("state") or "",
        "title": data.get("title") or "",
        "user": {"login": data.get("author_login") or "unknown"},
        "created_at": parse_iso_datetime(data.get("created_at")),
        "merged_at": parse_iso_datetime(data.get("merged_at")),
        "closed_at": parse_iso_datetime(data.get("closed_at")),
        "additions": data.get("additions", 0) or 0,
        "deletions": data.get("deletions", 0) or 0,
        "changed_files": data.get("changed_files", 0) or 0,
        "first_commit_at": parse_iso_datetime(data.get("first_commit_at")),
        "ready_for_review_at": parse_iso_datetime(data.get("ready_for_review_at")),
        "body": data.get("body"),
        "commit_messages": data.get("commit_messages") or [],
        "reviews": reviews,
    }


def review_from_dict(data: Mapping[str, Any]) -> Review:
    return {
        "user": {"login": data.get("author_login") or "unknown"},
        "state": data.get("state") or "",
        "submitted_at": parse_iso_datetime(data.get("submitted_at")),
    }

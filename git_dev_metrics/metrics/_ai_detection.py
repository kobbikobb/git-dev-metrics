"""AI co-author detection from PR bodies and commit messages."""

import re

from ..models import PullRequest

AI_TRAILER_PATTERNS = [
    r"Co-Authored-By:",
    r"co-authored-by:",
    r"Generated\s+(by|with|with\s+)?[\w\s]*AI",
    r"Claude\s+Code",
    r"Coding-Agent:",
    r"AI-assistant:",
    r"🤖\s*Generated",
    r"Aider:",
    r"Cursor:",
    r"GitHub\s+Copilot:",
    r"Devin:",
]


def is_ai_coauthored(pr: PullRequest) -> bool:
    texts = [pr.get("body") or "", *(pr.get("commit_messages") or [])]
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for text in texts
        if text
        for pattern in AI_TRAILER_PATTERNS
    )


def calculate_ai_percentage(prs: list[PullRequest]) -> float:
    if not prs:
        return 0.0
    ai_count = sum(1 for pr in prs if is_ai_coauthored(pr))
    return round((ai_count / len(prs)) * 100, 1)

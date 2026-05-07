"""Replace real GitHub logins with dev-1, dev-2, ... for safe team sharing."""


def _build_mapping(logins: list[str]) -> dict[str, str]:
    return {login: f"dev-{i + 1}" for i, login in enumerate(sorted(logins))}


def anonymize_metrics(metrics: dict) -> dict:
    """Return a new metrics dict with dev logins replaced by stable pseudonyms."""
    dev_metrics = metrics.get("dev_metrics") or {}
    reviewer_counts = metrics.get("reviewer_counts") or {}
    all_logins = set(dev_metrics) | set(reviewer_counts)
    mapping = _build_mapping(list(all_logins))

    return {
        **metrics,
        "dev_metrics": {mapping[d]: m for d, m in dev_metrics.items()},
        "reviewer_counts": {mapping[r]: c for r, c in reviewer_counts.items()},
        "_anonymize_mapping": mapping,
    }


def anonymize_stale_prs(stale_prs: list[dict], mapping: dict[str, str]) -> list[dict]:
    """Return new stale-PR rows with `author` swapped via the mapping."""
    rows = []
    for pr in stale_prs:
        author = pr.get("author", "")
        rows.append({**pr, "author": mapping.get(author, author)})
    return rows


__all__ = ["anonymize_metrics", "anonymize_stale_prs"]

from .health import calculate_dev_health_score


def build_summary(metrics: dict) -> dict:
    """Cross-format team summary used by console, markdown, and HTML outputs."""
    all_dev_metrics = list(metrics.get("dev_metrics", {}).values())
    health_by_dev = [calculate_dev_health_score(d, all_dev_metrics) for d in all_dev_metrics]
    team = metrics.get("team_metrics") or {}
    pr_count = int(team.get("pr_count", 0))
    total_reviews = int(team.get("reviews_given", 0))

    raw_counts = metrics.get("reviewer_counts")
    if raw_counts is None:
        raw_counts = {
            dev: m.get("reviews_given", 0) for dev, m in (metrics.get("dev_metrics") or {}).items()
        }
    reviewer_counts = {r: int(c) for r, c in raw_counts.items() if c}
    top_reviewer = ""
    max_review_share = 0
    if total_reviews > 0 and reviewer_counts:
        top_reviewer = max(sorted(reviewer_counts), key=lambda d: reviewer_counts[d])
        max_review_share = round(reviewer_counts[top_reviewer] / total_reviews * 100)

    return {
        "team_health": round(sum(health_by_dev) / len(health_by_dev)) if health_by_dev else 0,
        "total_prs": pr_count,
        "median_cycle": round(team.get("cycle_time", 0), 1),
        "median_pickup": round(team.get("pickup_time", 0), 1),
        "total_reviews": total_reviews,
        "ai_adoption": round(team.get("ai_percentage", 0)),
        "avg_lines_per_pr": round(team.get("avg_lines_per_pr", 0), 1),
        "review_ratio": round(total_reviews / pr_count, 2) if pr_count else 0.0,
        "top_reviewer": top_reviewer,
        "max_review_share": max_review_share,
    }


__all__ = ["build_summary"]

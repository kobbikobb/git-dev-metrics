from pathlib import Path

from ..health import calculate_health_score

REPO_COLUMNS = [
    "Repo",
    "Health",
    "Total PRs",
    "PRs/Week",
    "PR Size",
    "Avg Lines/PR",
    "Pickup Time (h)",
    "Review Time (h)",
    "Cycle Time (h)",
    "Reviews Given",
    "AI",
]


class FileRepoPrinter:
    """Print repo metrics to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_combined_metrics(
        self, metrics: dict, period: str, date_range: str | None = None
    ) -> None:
        header = (
            "| Repo | Health | Total PRs | PRs/Week | PR Size | Avg Lines/PR | "
            "Pickup Time (h) | Review Time (h) | Cycle Time (h) | Reviews Given | AI |"
        )
        separator = (
            "|------|--------|-----------|-----------|---------|--------------|"
            "------------------|-----------------|----------------|---------------|-----|"
        )
        title = (
            f"# Repo Metrics ({date_range})" if date_range else (f"# Repo Metrics (last {period})")
        )
        lines = ["", title, "", header, separator]
        active_repos = {
            name: m for name, m in metrics["repo_metrics"].items() if m.get("pr_count", 0) > 0
        }
        all_repo_metrics = list(active_repos.values())

        sorted_repos = []
        for repo_name, m in active_repos.items():
            health = calculate_health_score(m, all_repo_metrics)
            sorted_repos.append((repo_name, m, health))

        sorted_repos.sort(key=lambda x: x[2], reverse=True)

        for repo_name, m, health in sorted_repos:
            if health >= 80:
                emoji = "✅"
            elif health >= 60:
                emoji = "⚠️"
            else:
                emoji = "❌"
            row = (
                f"| {repo_name} | {emoji}{health} | "
                f"{m['pr_count']:.0f} | {m['prs_per_week']:.2f} | "
                f"{m['pr_size']:.1f} | {m.get('avg_lines_per_pr', 0):.1f} | "
                f"{m['pickup_time']:.2f} | {m['review_time']:.2f} | {m['cycle_time']:.2f} | "
                f"{m['reviews_given']:.0f} | {m['ai_percentage']:.0f}% |"
            )
            lines.append(row)

        lines.append("")
        self._write(lines)

    def _write(self, lines: list[str]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a") as f:
            f.write("\n".join(lines))

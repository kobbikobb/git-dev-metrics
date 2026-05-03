from pathlib import Path

from ..metrics.analyzer import build_summary_stats
from ..utils.date_utils import get_period_display_name
from .health import calculate_health_score, format_health, get_health_color

REPO_COLUMNS = [
    "Repo",
    "Health",
    "Pickup Time (h)",
    "Review Time (h)",
    "Cycle Time (h)",
    "PR Size",
    "Total PRs",
    "PRs/Week",
    "Reviews Given",
    "AI",
]


class ConsoleRepoPrinter:
    """Print repo metrics to console using Rich."""

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        stats = build_summary_stats(metrics)
        console.print(f"\n[bold]Team Health:[/bold] {stats['team_health']}")
        console.print(f"[bold]Total PRs:[/bold] {stats['total_prs']} across all repos")
        console.print(f"[bold]Avg PR Size:[/bold] {stats['avg_pr_size']} lines")
        console.print(f"[bold]Avg Cycle Time:[/bold] {stats['avg_cycle']}h (excl. inactive)")
        console.print(f"[bold]Avg Pickup Time:[/bold] {stats['avg_pickup']}h (excl. inactive)")
        console.print(f"[bold]Reviews Given:[/bold] {stats['total_reviews']} total team reviews")
        console.print(f"[bold]AI Adoption:[/bold] {stats['ai_adoption']}% average")

        table = Table(title=f"Repo Metrics ({get_period_display_name(period)})")
        for col in REPO_COLUMNS:
            table.add_column(col)

        all_repo_metrics = list(metrics["repo_metrics"].values())

        sorted_repos = []
        for repo_name, m in metrics["repo_metrics"].items():
            health = calculate_health_score(m, all_repo_metrics)
            sorted_repos.append((repo_name, m, health))

        sorted_repos.sort(key=lambda x: x[2], reverse=True)

        for repo_name, m, health in sorted_repos:
            color = get_health_color(health)
            table.add_row(
                repo_name,
                f"[{color}]{format_health(health)}[/{color}]",
                f"{m['pickup_time']:.2f}",
                f"{m['review_time']:.2f}",
                f"{m['cycle_time']:.2f}",
                f"{m['pr_size']:.1f}",
                f"{m['pr_count']:.0f}",
                f"{m['prs_per_week']:.2f}",
                f"{m['reviews_given']:.0f}",
                f"{m['ai_percentage']:.0f}%",
            )

        console.print("\n")
        console.print(table)


class FileRepoPrinter:
    """Print repo metrics to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        stats = build_summary_stats(metrics)
        lines = [
            f"# Repo Metrics ({get_period_display_name(period)})",
            "",
            "## Summary",
            "",
            f"**Team Health:** {stats['team_health']} average score",
            f"**Total PRs:** {stats['total_prs']} across all repos",
            f"**Avg PR Size:** {stats['avg_pr_size']} lines",
            f"**Avg Cycle Time:** {stats['avg_cycle']}h (excl. inactive)",
            f"**Avg Pickup Time:** {stats['avg_pickup']}h (excl. inactive)",
            f"**Reviews Given:** {stats['total_reviews']} total team reviews",
            f"**AI Adoption:** {stats['ai_adoption']}% average",
            "",
        ]

        header = (
            "| Repo | Health | Pickup Time (h) | Review Time (h) | Cycle Time (h) | "
            "PR Size | Total PRs | PRs/Week | Reviews Given | AI |"
        )
        separator = (
            "|------|--------|------------------|-----------------|----------------|"
            "---------|-----------|-----------|---------------|-----|"
        )
        lines.extend([header, separator])

        all_repo_metrics = list(metrics["repo_metrics"].values())

        sorted_repos = []
        for repo_name, m in metrics["repo_metrics"].items():
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
                f"| {repo_name} | {emoji}{health} | {m['pickup_time']:.2f} | "
                f"{m['review_time']:.2f} | {m['cycle_time']:.2f} | {m['pr_size']:.1f} | "
                f"{m['pr_count']:.0f} | {m['prs_per_week']:.2f} | {m['reviews_given']:.0f} | "
                f"{m['ai_percentage']:.0f}% |"
            )
            lines.append(row)

        lines.append("")
        self._write(lines)

    def _write(self, lines: list[str]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a") as f:
            f.write("\n".join(lines))

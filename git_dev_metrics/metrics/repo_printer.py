from pathlib import Path

from .calculator import calculate_health_score

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
]


def _get_health_color(score: int) -> str:
    """Return color for health score."""
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


class ConsoleRepoPrinter:
    """Print repo metrics to console using Rich."""

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Repo Metrics (last {period})")
        for col in REPO_COLUMNS:
            table.add_column(col)

        all_repo_metrics = list(metrics["repo_metrics"].values())

        sorted_repos = []
        for repo_name, m in metrics["repo_metrics"].items():
            health = calculate_health_score(m, all_repo_metrics)
            sorted_repos.append((repo_name, m, health))

        sorted_repos.sort(key=lambda x: x[2])

        for repo_name, m, health in sorted_repos:
            color = _get_health_color(health)
            table.add_row(
                repo_name,
                f"[{color}]{health}[/{color}]",
                f"{m['pickup_time']:.2f}",
                f"{m['review_time']:.2f}",
                f"{m['cycle_time']:.2f}",
                f"{m['pr_size']:.1f}",
                f"{m['pr_count']:.0f}",
                f"{m['prs_per_week']:.2f}",
                f"{m['reviews_given']:.0f}",
            )

        console.print("\n")
        console.print(table)


class FileRepoPrinter:
    """Print repo metrics to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        header = (
            "| Repo | Health | Pickup Time (h) | Review Time (h) | Cycle Time (h) | "
            "PR Size | Total PRs | PRs/Week | Reviews Given |"
        )
        separator = (
            "|------|--------|------------------|-----------------|----------------|"
            "---------|-----------|-----------|---------------|"
        )
        lines = [f"# Repo Metrics (last {period})", "", header, separator]

        all_repo_metrics = list(metrics["repo_metrics"].values())

        sorted_repos = []
        for repo_name, m in metrics["repo_metrics"].items():
            health = calculate_health_score(m, all_repo_metrics)
            sorted_repos.append((repo_name, m, health))

        sorted_repos.sort(key=lambda x: x[2])

        for repo_name, m, health in sorted_repos:
            emoji = "✅" if health >= 80 else "⚠️" if health >= 60 else "❌"
            row = (
                f"| {repo_name} | {emoji}{health} | {m['pickup_time']:.2f} | "
                f"{m['review_time']:.2f} | {m['cycle_time']:.2f} | {m['pr_size']:.1f} | "
                f"{m['pr_count']:.0f} | {m['prs_per_week']:.2f} | {m['reviews_given']:.0f} |"
            )
            lines.append(row)

        lines.append("")
        self._write(lines)

    def _write(self, lines: list[str]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a") as f:
            f.write("\n".join(lines))

from pathlib import Path


class ConsoleRepoPrinter:
    """Print repo metrics to console using Rich."""

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Repo Metrics (last {period})")
        for col in [
            "Repo",
            "Pickup Time (h)",
            "Review Time (h)",
            "Cycle Time (h)",
            "PR Size",
            "Total PRs",
            "PRs/Week",
            "Reviews Given",
        ]:
            table.add_column(col)

        for repo_name, m in sorted(
            metrics["repo_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            table.add_row(
                repo_name,
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
            "| Repo | Pickup Time (h) | Review Time (h) | Cycle Time (h) | "
            "PR Size | Total PRs | PRs/Week | Reviews Given |"
        )
        separator = (
            "|------|------------------|-----------------|----------------|"
            "---------|-----------|-----------|---------------|"
        )
        lines = [f"# Repo Metrics (last {period})", "", header, separator]

        for repo_name, m in sorted(
            metrics["repo_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            lines.append(
                f"| {repo_name} | {m['pickup_time']:.2f} | {m['review_time']:.2f} | "
                f"{m['cycle_time']:.2f} | {m['pr_size']:.1f} | {m['pr_count']:.0f} | "
                f"{m['prs_per_week']:.2f} | {m['reviews_given']:.0f} |"
            )

        lines.append("")
        self._write(lines)

    def _write(self, lines: list[str]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a") as f:
            f.write("\n".join(lines))

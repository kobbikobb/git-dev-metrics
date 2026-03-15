from pathlib import Path

from .calculator import calculate_health_score

DEV_COLUMNS = [
    "Dev",
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


class ConsoleDevPrinter:
    """Print dev metrics to console using Rich."""

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Developer Metrics (combined)")
        for col in DEV_COLUMNS:
            table.add_column(col)

        all_dev_metrics = list(metrics["dev_metrics"].values())

        for dev, m in sorted(
            metrics["dev_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            health = calculate_health_score(m, all_dev_metrics)
            color = _get_health_color(health)
            table.add_row(
                dev,
                f"[{color}]{health}[/{color}]",
                f"{m['pickup_time']:.2f}",
                f"{m['review_time']:.2f}",
                f"{m['cycle_time']:.2f}",
                f"{m['pr_size']:.1f}",
                f"{m['pr_count']:.0f}",
                f"{m['prs_per_week']:.2f}",
                f"{m['reviews_given']:.0f}",
            )

        console.print(table)


class FileDevPrinter:
    """Print dev metrics to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        header = (
            "| Dev | Health | Pickup Time (h) | Review Time (h) | Cycle Time (h) | "
            "PR Size | Total PRs | PRs/Week | Reviews Given |"
        )
        separator = (
            "|------|--------|------------------|-----------------|----------------|"
            "---------|-----------|-----------|---------------|"
        )
        lines = ["", "# Developer Metrics (combined)", "", header, separator]

        all_dev_metrics = list(metrics["dev_metrics"].values())

        for dev, m in sorted(
            metrics["dev_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            health = calculate_health_score(m, all_dev_metrics)
            emoji = "✅" if health >= 80 else "⚠️" if health >= 60 else "❌"
            row = (
                f"| {dev} | {emoji}{health} | {m['pickup_time']:.2f} | "
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

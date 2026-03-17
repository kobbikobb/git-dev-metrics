from pathlib import Path

from .health import calculate_health_score, format_health, get_health_color

LABEL_COLUMNS = [
    "Label",
    "Health",
    "Pickup Time (h)",
    "Review Time (h)",
    "Cycle Time (h)",
    "PR Size",
    "Total PRs",
    "PRs/Week",
]


def _sort_by_health(metrics: dict) -> list[tuple]:
    """Sort metrics by health score descending."""
    all_metrics = list(metrics.values())
    sorted_items = []
    for label, m in metrics.items():
        health = calculate_health_score(m, all_metrics)
        sorted_items.append((label, m, health))
    sorted_items.sort(key=lambda x: x[2], reverse=True)
    return sorted_items


class ConsoleLabelPrinter:
    """Print label metrics to console using Rich."""

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Label Metrics (combined)")
        for col in LABEL_COLUMNS:
            table.add_column(col)

        for label, m, health in _sort_by_health(metrics["label_metrics"]):
            color = get_health_color(health)
            table.add_row(
                label,
                f"[{color}]{format_health(health)}[/{color}]",
                f"{m['pickup_time']:.2f}",
                f"{m['review_time']:.2f}",
                f"{m['cycle_time']:.2f}",
                f"{m['pr_size']:.1f}",
                f"{m['pr_count']:.0f}",
                f"{m['prs_per_week']:.2f}",
            )

        console.print(table)


class FileLabelPrinter:
    """Print label metrics to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        header = (
            "| Label | Health | Pickup Time (h) | Review Time (h) | Cycle Time (h) | "
            "PR Size | Total PRs | PRs/Week |"
        )
        separator = (
            "|------|--------|------------------|-----------------|----------------|"
            "---------|-----------|-----------|"
        )
        lines = ["", "# Label Metrics (combined)", "", header, separator]

        for label, m, health in _sort_by_health(metrics["label_metrics"]):
            if health >= 80:
                emoji = "✅"
            elif health >= 60:
                emoji = "⚠️"
            else:
                emoji = "❌"
            row = (
                f"| {label} | {emoji}{health} | {m['pickup_time']:.2f} | "
                f"{m['review_time']:.2f} | {m['cycle_time']:.2f} | {m['pr_size']:.1f} | "
                f"{m['pr_count']:.0f} | {m['prs_per_week']:.2f} |"
            )
            lines.append(row)

        lines.append("")
        self._write(lines)

    def _write(self, lines: list[str]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a") as f:
            f.write("\n".join(lines))

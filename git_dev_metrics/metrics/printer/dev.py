from .._rows import band_color
from ..snapshot import MetricsSnapshot

DEV_COLUMNS = [
    "Dev",
    "Health",
    "Pickup Time (h)",
    "Review Time (h)",
    "Cycle Time (h)",
    "PR Size",
    "Avg Lines/PR",
    "Total PRs",
    "PRs/Week",
    "Reviews Given",
    "AI",
]


class ConsoleDevPrinter:
    """Print dev metrics to console using Rich."""

    def print_combined_metrics(
        self, snapshot: MetricsSnapshot, period: str, date_range: str | None = None
    ) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        title = (
            f"Developer Metrics ({date_range})" if date_range else ("Developer Metrics (combined)")
        )
        if snapshot.has_partial:
            title += " (partial data)"
        table = Table(title=title)
        for col in DEV_COLUMNS:
            table.add_column(col)

        for row in snapshot.devs:
            color = band_color(row.band)
            table.add_row(
                row.name,
                f"[{color}]{row.health}[/{color}]",
                f"{row.pickup_time:.2f}",
                f"{row.review_time:.2f}",
                f"{row.cycle_time:.2f}",
                f"{row.pr_size:.1f}",
                f"{row.avg_lines_per_pr:.1f}",
                f"{row.pr_count:.0f}",
                f"{row.prs_per_week:.2f}",
                f"{row.reviews_given:.0f}",
                f"{row.ai_percentage:.0f}%",
            )

        console.print(table)

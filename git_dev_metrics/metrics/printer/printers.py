from ..snapshot import MetricsSnapshot
from .dev import ConsoleDevPrinter


class ConsolePrinter:
    """Print metrics to console."""

    def __init__(self) -> None:
        self._dev_printer = ConsoleDevPrinter()

    def print_combined_metrics(
        self, snapshot: MetricsSnapshot, period: str, date_range: str
    ) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        team = snapshot.team
        summary = snapshot.summary
        cells = [
            ("Team Health", str(team.health)),
            ("Total PRs", str(team.pr_count)),
            ("Median Lines/PR", str(round(team.pr_size, 1))),
            ("Median Cycle (h)", str(round(team.cycle_time, 1))),
            ("Median Pickup (h)", str(round(team.pickup_time, 1))),
            ("PRs/Week per Dev", str(round(team.prs_per_week, 2))),
            ("Total Reviews", str(team.reviews_given)),
            ("AI Adoption", f"{round(team.ai_percentage)}%"),
            ("Review Ratio", f"{summary.review_ratio}x"),
            ("Top Reviewer", summary.top_reviewer or "—"),
            ("Max Review Share", f"{summary.max_review_share}%"),
        ]

        console.print()
        chunk_size = 6
        for chunk_start in range(0, len(cells), chunk_size):
            chunk = cells[chunk_start : chunk_start + chunk_size]
            table = Table(
                title=f"Summary ({date_range})" if chunk_start == 0 else None,
                show_header=True,
                header_style="bold",
            )
            for label, _ in chunk:
                table.add_column(label, justify="left")
            table.add_row(*(value for _, value in chunk))
            console.print(table)
        console.print()

        self._dev_printer.print_combined_metrics(snapshot, period, date_range)


__all__ = ["ConsolePrinter"]

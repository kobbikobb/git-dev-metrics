from ..summary import build_summary
from .base import Printer
from .dev import ConsoleDevPrinter


class ConsolePrinter(Printer):
    """Print metrics to console."""

    def __init__(self) -> None:
        self._dev_printer = ConsoleDevPrinter()

    def print_combined_metrics(self, metrics: dict, period: str, date_range: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        summary = build_summary(metrics)
        cells = [
            ("Team Health", str(summary["team_health"])),
            ("Total PRs", str(summary["total_prs"])),
            ("Median Lines/PR", str(summary["median_lines_per_pr"])),
            ("Median Cycle (h)", str(summary["median_cycle"])),
            ("Median Pickup (h)", str(summary["median_pickup"])),
            ("PRs/Week per Dev", str(summary["median_prs_per_week"])),
            ("Total Reviews", str(summary["total_reviews"])),
            ("AI Adoption", f"{summary['ai_adoption']}%"),
            ("Review Ratio", f"{summary['review_ratio']}x"),
            ("Top Reviewer", summary["top_reviewer"] or "—"),
            ("Max Review Share", f"{summary['max_review_share']}%"),
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

        self._dev_printer.print_combined_metrics(metrics, period, date_range)


__all__ = ["ConsolePrinter", "Printer"]

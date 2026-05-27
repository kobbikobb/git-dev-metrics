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
            ("Top Reviewer", summary.top_reviewer or "\u2014"),
            ("Max Review Share", f"{summary.max_review_share}%"),
        ]

        console.print()
        self._render_table(cells, date_range, snapshot.has_partial, console)
        console.print()

        self._dev_printer.print_combined_metrics(snapshot, period, date_range)

    def _render_table(
        self, cells: list[tuple[str, str]], date_range: str, has_partial: bool, console
    ) -> None:
        from rich.table import Table

        title = f"Summary ({date_range})"
        if has_partial:
            title += " (partial data)"

        chunk_size = 6
        for chunk_start in range(0, len(cells), chunk_size):
            chunk = cells[chunk_start : chunk_start + chunk_size]
            table = Table(
                title=title if chunk_start == 0 else None,
                show_header=True,
                header_style="bold",
            )
            for label, _ in chunk:
                table.add_column(label, justify="left")
            table.add_row(*(value for _, value in chunk))
            console.print(table)


__all__ = ["ConsolePrinter"]

from ..snapshot import MetricsSnapshot
from .dev import ConsoleDevPrinter


class ConsolePrinter:
    """Print metrics to console."""

    def __init__(self) -> None:
        self._dev_printer = ConsoleDevPrinter()

    def print_combined_metrics(
        self, snapshot: MetricsSnapshot, date_range: str
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

        console.print()

        self._dev_printer.print_combined_metrics(snapshot, date_range)


__all__ = ["ConsolePrinter"]

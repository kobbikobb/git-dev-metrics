from pathlib import Path

from ..dev_printer import ConsoleDevPrinter, FileDevPrinter
from ..repo_printer import FileRepoPrinter
from .base import Printer
from .html_printer import FileHtmlPrinter, build_summary
from .stale_printer import FileStalePRPrinter
from .utils import get_default_output_path


class ConsolePrinter(Printer):
    """Print metrics to console."""

    def __init__(self) -> None:
        self._dev_printer = ConsoleDevPrinter()

    def print_combined_metrics(self, metrics: dict, period: str, date_range: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        summary = build_summary(metrics)
        table = Table(title=f"Summary ({date_range})")
        for col in (
            "Team Health",
            "Total PRs",
            "Avg Lines/PR",
            "Avg Cycle (h)",
            "Avg Pickup (h)",
            "Reviews",
            "AI",
        ):
            table.add_column(col)
        table.add_row(
            str(summary["team_health"]),
            str(summary["total_prs"]),
            str(summary["avg_lines_per_pr"]),
            str(summary["avg_cycle"]),
            str(summary["avg_pickup"]),
            str(summary["total_reviews"]),
            f"{summary['ai_adoption']}%",
        )

        console.print()
        console.print(table)
        console.print()

        self._dev_printer.print_combined_metrics(metrics, period, date_range)


class FilePrinter(Printer):
    """Print metrics to markdown file."""

    def __init__(self, output_path: Path | None = None) -> None:
        self._path = output_path or get_default_output_path()
        self._repo_printer = FileRepoPrinter(self._path)
        self._dev_printer = FileDevPrinter(self._path)

    def print_combined_metrics(self, metrics: dict, period: str, date_range: str) -> None:
        summary = build_summary(metrics)
        lines = [
            f"# Summary ({date_range})",
            "",
            f"- **Team Health:** {summary['team_health']}",
            f"- **Total PRs:** {summary['total_prs']}",
            f"- **Avg Lines/PR:** {summary['avg_lines_per_pr']}",
            f"- **Avg Cycle Time:** {summary['avg_cycle']}h",
            f"- **Avg Pickup Time:** {summary['avg_pickup']}h",
            f"- **Total Reviews:** {summary['total_reviews']}",
            f"- **AI Adoption:** {summary['ai_adoption']}%",
            "",
        ]
        self._write(lines)
        self._repo_printer.print_combined_metrics(metrics, period, date_range)
        self._dev_printer.print_combined_metrics(metrics, period, date_range)

    def _write(self, lines: list[str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a") as f:
            f.write("\n".join(lines))


class CompositePrinter(Printer):
    """Print metrics to both console and file."""

    def __init__(self, output_path: Path | None = None) -> None:
        self._console_printer = ConsolePrinter()
        self._file_printer = FilePrinter(output_path)
        self._html_printer = FileHtmlPrinter(output_path or get_default_output_path())
        self._file_stale_printer = FileStalePRPrinter(output_path or get_default_output_path())

    def print_combined_metrics(self, metrics: dict, period: str, date_range: str) -> None:
        self._console_printer.print_combined_metrics(metrics, period, date_range)
        self._file_printer.print_combined_metrics(metrics, period, date_range)
        self._html_printer.print_combined_metrics(metrics, period, date_range)

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        self._file_stale_printer.print_stale_prs(stale_prs)


def print_combined_metrics(
    metrics: dict,
    period: str,
    output_path: Path | None = None,
    date_range: str | None = None,
) -> None:
    """Print metrics to console and file."""
    CompositePrinter(output_path).print_combined_metrics(metrics, period, date_range or period)


def print_stale_prs(stale_prs: list[dict], output_path: Path | None = None) -> None:
    """Print stale PRs to console and file."""
    CompositePrinter(output_path).print_stale_prs(stale_prs)


__all__ = [
    "Printer",
    "ConsolePrinter",
    "FilePrinter",
    "CompositePrinter",
    "print_combined_metrics",
    "print_stale_prs",
]

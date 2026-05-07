from pathlib import Path

from ..summary import build_summary
from .base import Printer
from .dev import ConsoleDevPrinter, FileDevPrinter
from .html import FileHtmlPrinter
from .repo import FileRepoPrinter
from .stale import FileStalePRPrinter
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
        cells = [
            ("Team Health", str(summary["team_health"])),
            ("Total PRs", str(summary["total_prs"])),
            ("PRs/Week per Dev", str(summary["median_prs_per_week"])),
            ("Median Lines/PR", str(summary["median_lines_per_pr"])),
            ("Median Pickup (h)", str(summary["median_pickup"])),
            ("Median Cycle (h)", str(summary["median_cycle"])),
            ("Total Reviews", str(summary["total_reviews"])),
            ("Review Ratio", f"{summary['review_ratio']}x"),
            ("Top Reviewer", summary["top_reviewer"] or "—"),
            ("Max Review Share", f"{summary['max_review_share']}%"),
            ("AI Adoption", f"{summary['ai_adoption']}%"),
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
            f"- **PRs/Week per Dev:** {summary['median_prs_per_week']}",
            f"- **Median Lines/PR:** {summary['median_lines_per_pr']}",
            f"- **Median Pickup Time:** {summary['median_pickup']}h",
            f"- **Median Cycle Time:** {summary['median_cycle']}h",
            f"- **Total Reviews:** {summary['total_reviews']}",
            f"- **Review Ratio:** {summary['review_ratio']}x",
            f"- **Top Reviewer:** {summary['top_reviewer'] or '—'}",
            f"- **Max Review Share:** {summary['max_review_share']}%",
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

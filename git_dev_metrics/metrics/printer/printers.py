from pathlib import Path

from ..dev_printer import ConsoleDevPrinter, FileDevPrinter
from ..label_printer import ConsoleLabelPrinter, FileLabelPrinter
from ..repo_printer import ConsoleRepoPrinter, FileRepoPrinter
from .base import Printer
from .html_printer import FileHtmlPrinter, build_summary
from .stale_printer import ConsoleStalePRPrinter, FileStalePRPrinter
from .utils import get_default_output_path


class ConsolePrinter(Printer):
    """Print metrics to console."""

    def __init__(self) -> None:
        self._repo_printer = ConsoleRepoPrinter()
        self._dev_printer = ConsoleDevPrinter()
        self._label_printer = ConsoleLabelPrinter()

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        summary = build_summary(metrics)
        panel = Panel(
            f"Team Health: {summary['team_health']}  |  "
            f"Total PRs: {summary['total_prs']}  |  "
            f"Avg Cycle: {summary['avg_cycle']}h  |  "
            f"Avg Pickup: {summary['avg_pickup']}h  |  "
            f"Reviews: {summary['total_reviews']}  |  "
            f"AI: {summary['ai_adoption']}%",
            title=f"Summary (last {period})",
            expand=False,
        )
        console.print(panel)
        console.print()

        self._repo_printer.print_combined_metrics(metrics, period)
        self._dev_printer.print_combined_metrics(metrics, period)
        if "label_metrics" in metrics and metrics["label_metrics"]:
            self._label_printer.print_combined_metrics(metrics, period)


class FilePrinter(Printer):
    """Print metrics to markdown file."""

    def __init__(self, output_path: Path | None = None) -> None:
        path = output_path or get_default_output_path()
        self._repo_printer = FileRepoPrinter(path)
        self._dev_printer = FileDevPrinter(path)
        self._label_printer = FileLabelPrinter(path)

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        summary = build_summary(metrics)
        lines = [
            f"# Summary (last {period})",
            "",
            f"- **Team Health:** {summary['team_health']}",
            f"- **Total PRs:** {summary['total_prs']}",
            f"- **Avg Cycle Time:** {summary['avg_cycle']}h",
            f"- **Avg Pickup Time:** {summary['avg_pickup']}h",
            f"- **Total Reviews:** {summary['total_reviews']}",
            f"- **AI Adoption:** {summary['ai_adoption']}%",
            "",
        ]
        self._write(lines)
        self._repo_printer.print_combined_metrics(metrics, period)
        self._dev_printer.print_combined_metrics(metrics, period)
        if "label_metrics" in metrics and metrics["label_metrics"]:
            self._label_printer.print_combined_metrics(metrics, period)

    def _write(self, lines: list[str]) -> None:

        output_path = get_default_output_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "a") as f:
            f.write("\n".join(lines))


class CompositePrinter(Printer):
    """Print metrics to both console and file."""

    def __init__(self, output_path: Path | None = None) -> None:
        self._console_printer = ConsolePrinter()
        self._file_printer = FilePrinter(output_path)
        self._html_printer = FileHtmlPrinter(output_path or get_default_output_path())
        self._console_stale_printer = ConsoleStalePRPrinter()
        self._file_stale_printer = FileStalePRPrinter(output_path or get_default_output_path())

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._console_printer.print_combined_metrics(metrics, period)
        self._file_printer.print_combined_metrics(metrics, period)
        self._html_printer.print_combined_metrics(metrics, period)

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        self._console_stale_printer.print_stale_prs(stale_prs)
        self._file_stale_printer.print_stale_prs(stale_prs)


def print_combined_metrics(metrics: dict, period: str, output_path: Path | None = None) -> None:
    """Print metrics to console and file."""
    CompositePrinter(output_path).print_combined_metrics(metrics, period)


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

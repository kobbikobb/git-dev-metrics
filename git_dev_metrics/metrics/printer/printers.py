from pathlib import Path

from ..dev_printer import ConsoleDevPrinter, FileDevPrinter
from ..repo_printer import ConsoleRepoPrinter, FileRepoPrinter
from .base import Printer
from .bottleneck_printer import ConsoleBottleneckPrinter, FileBottleneckPrinter
from .stale_printer import ConsoleStalePRPrinter, FileStalePRPrinter
from .utils import get_default_output_path


class ConsolePrinter(Printer):
    """Print metrics to console."""

    def __init__(self) -> None:
        self._repo_printer = ConsoleRepoPrinter()
        self._dev_printer = ConsoleDevPrinter()

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._repo_printer.print_combined_metrics(metrics, period)
        self._dev_printer.print_combined_metrics(metrics, period)


class FilePrinter(Printer):
    """Print metrics to markdown file."""

    def __init__(self, output_path: Path | None = None) -> None:
        path = output_path or get_default_output_path()
        self._repo_printer = FileRepoPrinter(path)
        self._dev_printer = FileDevPrinter(path)

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._repo_printer.print_combined_metrics(metrics, period)
        self._dev_printer.print_combined_metrics(metrics, period)


class CompositePrinter(Printer):
    """Print metrics to both console and file."""

    def __init__(self, output_path: Path | None = None) -> None:
        self._console_printer = ConsolePrinter()
        self._file_printer = FilePrinter(output_path)
        self._console_stale_printer = ConsoleStalePRPrinter()
        self._file_stale_printer = FileStalePRPrinter(output_path or get_default_output_path())
        self._console_bottleneck_printer = ConsoleBottleneckPrinter()
        self._file_bottleneck_printer = FileBottleneckPrinter(
            output_path or get_default_output_path()
        )

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._console_printer.print_combined_metrics(metrics, period)
        self._file_printer.print_combined_metrics(metrics, period)

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        self._console_stale_printer.print_stale_prs(stale_prs)
        self._file_stale_printer.print_stale_prs(stale_prs)

    def print_draft_prs(self, prs: list[dict]) -> None:
        self._console_bottleneck_printer.print_draft_prs(prs)
        self._file_bottleneck_printer.print_draft_prs(prs)

    def print_awaiting_review_prs(self, prs: list[dict]) -> None:
        self._console_bottleneck_printer.print_awaiting_review_prs(prs)
        self._file_bottleneck_printer.print_awaiting_review_prs(prs)


def print_combined_metrics(metrics: dict, period: str, output_path: Path | None = None) -> None:
    """Print metrics to console and file."""
    CompositePrinter(output_path).print_combined_metrics(metrics, period)


def print_stale_prs(stale_prs: list[dict], output_path: Path | None = None) -> None:
    """Print stale PRs to console and file."""
    CompositePrinter(output_path).print_stale_prs(stale_prs)


def print_bottleneck_prs(
    draft_prs: list[dict],
    awaiting_review_prs: list[dict],
    output_path: Path | None = None,
) -> None:
    """Print bottleneck PRs to console and file."""
    printer = CompositePrinter(output_path)
    printer.print_draft_prs(draft_prs)
    printer.print_awaiting_review_prs(awaiting_review_prs)


__all__ = [
    "Printer",
    "ConsolePrinter",
    "FilePrinter",
    "CompositePrinter",
    "print_combined_metrics",
    "print_stale_prs",
    "print_bottleneck_prs",
]

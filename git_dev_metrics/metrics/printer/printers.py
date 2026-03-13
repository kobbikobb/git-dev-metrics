from pathlib import Path

from ..dev_printer import ConsoleDevPrinter, FileDevPrinter
from ..repo_printer import ConsoleRepoPrinter, FileRepoPrinter
from .base import Printer
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

    def __init__(self, output_path: Path) -> None:
        self._repo_printer = FileRepoPrinter(output_path)
        self._dev_printer = FileDevPrinter(output_path)

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._repo_printer.print_combined_metrics(metrics, period)
        self._dev_printer.print_combined_metrics(metrics, period)


class CompositePrinter(Printer):
    """Print metrics to both console and file."""

    def __init__(self, output_path: Path | None = None) -> None:
        self._console_printer = ConsolePrinter()
        self._file_printer = FilePrinter(output_path or get_default_output_path())
        self._console_stale_printer = ConsoleStalePRPrinter()
        self._file_stale_printer: FileStalePRPrinter | None = None

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._console_printer.print_combined_metrics(metrics, period)
        self._file_printer.print_combined_metrics(metrics, period)

    def print_stale_prs(self, stale_prs: list[dict], output_path: Path | None = None) -> None:
        self._console_stale_printer.print_stale_prs(stale_prs)
        path = output_path or get_default_output_path()
        FileStalePRPrinter(path).print_stale_prs(stale_prs)


__all__ = [
    "Printer",
    "ConsolePrinter",
    "FilePrinter",
    "CompositePrinter",
    "get_default_output_path",
]

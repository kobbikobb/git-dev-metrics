from abc import ABC, abstractmethod
from pathlib import Path


class Printer(ABC):
    """Abstract base class for printing combined metrics."""

    @abstractmethod
    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        """Print both repo and dev metrics."""
        pass


class ConsolePrinter(Printer):
    """Print metrics to console."""

    def __init__(self):
        from .dev_printer import ConsoleDevPrinter
        from .repo_printer import ConsoleRepoPrinter

        self._repo_printer = ConsoleRepoPrinter()
        self._dev_printer = ConsoleDevPrinter()

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._repo_printer.print(metrics, period)
        self._dev_printer.print(metrics, period)


class FilePrinter(Printer):
    """Print metrics to markdown file."""

    def __init__(self, output_path: Path):
        from .dev_printer import FileDevPrinter
        from .repo_printer import FileRepoPrinter

        self._repo_printer = FileRepoPrinter(output_path)
        self._dev_printer = FileDevPrinter(output_path)

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._repo_printer.print(metrics, period)
        self._dev_printer.print(metrics, period)


class CompositePrinter(Printer):
    """Print metrics to both console and file."""

    def __init__(self, output_path: Path):
        self._console_printer = ConsolePrinter()
        self._file_printer = FilePrinter(output_path)

    def print_combined_metrics(self, metrics: dict, period: str) -> None:
        self._console_printer.print_combined_metrics(metrics, period)
        self._file_printer.print_combined_metrics(metrics, period)


def get_default_output_path() -> Path:
    """Get default output path with timestamp."""
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path(f"./metrics_results/metrics_{timestamp}.md")

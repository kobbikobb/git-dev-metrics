from ..snapshot import MetricsSnapshot
from .dev import ConsoleDevPrinter


class ConsolePrinter:
    """Print metrics to console."""

    def __init__(self) -> None:
        self._dev_printer = ConsoleDevPrinter()

    def print_combined_metrics(
        self,
        snapshot: MetricsSnapshot,
        date_range: str,
        nicknames: dict[str, str] | None = None,
    ) -> None:
        from rich.console import Console

        console = Console()
        console.print()
        console.print()

        self._dev_printer.print_combined_metrics(snapshot, date_range, nicknames=nicknames)


__all__ = ["ConsolePrinter"]

from .._rows import team_target_status
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
        targets: dict[str, float] | None = None,
    ) -> None:
        from rich.console import Console
        from rich.text import Text

        console = Console()
        console.print()
        console.print()

        self._dev_printer.print_combined_metrics(snapshot, date_range, nicknames=nicknames)

        if targets:
            status = team_target_status(snapshot.team, targets)
            if status["total"] > 0:
                parts = [f"[bold]Targets:[/bold] {status['met']}/{status['total']} met"]
                for item in status["items"]:
                    icon = "✓" if item["ok"] else "✗"
                    color = "green" if item["ok"] else "red"
                    parts.append(
                        f"[{color}]{icon}[/{color}] {item['label']} "
                        f"{item['actual']}{item['unit']} / {item['target']}{item['unit']}"
                    )
                console.print(Text.from_markup(" · ".join(parts)))
                console.print()


__all__ = ["ConsolePrinter"]

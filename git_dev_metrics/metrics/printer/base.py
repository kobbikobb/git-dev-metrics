from abc import ABC, abstractmethod

from ..snapshot import MetricsSnapshot


class Printer(ABC):
    """Abstract base class for printing combined metrics."""

    @abstractmethod
    def print_combined_metrics(
        self, snapshot: MetricsSnapshot, period: str, date_range: str
    ) -> None:
        """Print both repo and dev metrics."""
        ...

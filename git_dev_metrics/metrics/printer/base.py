from abc import ABC, abstractmethod


class Printer(ABC):
    """Abstract base class for printing combined metrics."""

    @abstractmethod
    def print_combined_metrics(self, metrics: dict, period: str, date_range: str) -> None:
        """Print both repo and dev metrics."""
        ...

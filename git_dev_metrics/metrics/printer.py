from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class Printer(ABC):
    """Abstract base class for printers."""

    @abstractmethod
    def print_repo_metrics(self, metrics: dict, period: str) -> None:
        pass

    @abstractmethod
    def print_dev_metrics(self, metrics: dict, period: str) -> None:
        pass


class ConsolePrinter(Printer):
    """Print metrics to console using Rich."""

    def print_repo_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Repo Metrics (last {period})")
        for col in [
            "Repo",
            "Pickup Time (h)",
            "Review Time (h)",
            "Cycle Time (h)",
            "PR Size",
            "Total PRs",
            "PRs/Week",
            "Reviews Given",
        ]:
            table.add_column(col)

        for repo_name, m in sorted(
            metrics["repo_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            table.add_row(
                repo_name,
                f"{m['pickup_time']:.2f}",
                f"{m['review_time']:.2f}",
                f"{m['cycle_time']:.2f}",
                f"{m['pr_size']:.1f}",
                f"{m['pr_count']:.0f}",
                f"{m['prs_per_week']:.2f}",
                f"{m['reviews_given']:.0f}",
            )

        console.print("\n")
        console.print(table)

    def print_dev_metrics(self, metrics: dict, period: str) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Developer Metrics (combined)")
        for col in [
            "Dev",
            "Pickup Time (h)",
            "Review Time (h)",
            "Cycle Time (h)",
            "PR Size",
            "Total PRs",
            "PRs/Week",
            "Reviews Given",
        ]:
            table.add_column(col)

        for dev, m in sorted(
            metrics["dev_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            table.add_row(
                dev,
                f"{m['pickup_time']:.2f}",
                f"{m['review_time']:.2f}",
                f"{m['cycle_time']:.2f}",
                f"{m['pr_size']:.1f}",
                f"{m['pr_count']:.0f}",
                f"{m['prs_per_week']:.2f}",
                f"{m['reviews_given']:.0f}",
            )

        console.print(table)


class FilePrinter(Printer):
    """Print metrics to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_repo_metrics(self, metrics: dict, period: str) -> None:
        header = (
            "| Repo | Pickup Time (h) | Review Time (h) | Cycle Time (h) | "
            "PR Size | Total PRs | PRs/Week | Reviews Given |"
        )
        separator = (
            "|------|------------------|-----------------|----------------|"
            "---------|-----------|-----------|---------------|"
        )
        lines = [f"# Repo Metrics (last {period})", "", header, separator]

        for repo_name, m in sorted(
            metrics["repo_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            lines.append(
                f"| {repo_name} | {m['pickup_time']:.2f} | {m['review_time']:.2f} | "
                f"{m['cycle_time']:.2f} | {m['pr_size']:.1f} | {m['pr_count']:.0f} | "
                f"{m['prs_per_week']:.2f} | {m['reviews_given']:.0f} |"
            )

        lines.append("")
        self._write_lines(lines)

    def print_dev_metrics(self, metrics: dict, period: str) -> None:
        header = (
            "| Dev | Pickup Time (h) | Review Time (h) | Cycle Time (h) | "
            "PR Size | Total PRs | PRs/Week | Reviews Given |"
        )
        separator = (
            "|-----|------------------|-----------------|----------------|"
            "---------|-----------|-----------|---------------|"
        )
        lines = ["", "# Developer Metrics (combined)", "", header, separator]

        for dev, m in sorted(
            metrics["dev_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
        ):
            lines.append(
                f"| {dev} | {m['pickup_time']:.2f} | {m['review_time']:.2f} | "
                f"{m['cycle_time']:.2f} | {m['pr_size']:.1f} | {m['pr_count']:.0f} | "
                f"{m['prs_per_week']:.2f} | {m['reviews_given']:.0f} |"
            )

        lines.append("")
        self._write_lines(lines)

    def _write_lines(self, lines: list[str]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "a") as f:
            f.write("\n".join(lines))


def print_combined_metrics(printer: Printer, metrics: dict, period: str) -> None:
    """Print combined metrics using the given printer."""
    printer.print_repo_metrics(metrics, period)
    printer.print_dev_metrics(metrics, period)


def get_default_output_path() -> Path:
    """Get default output path with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path(f"./metrics_results/metrics_{timestamp}.md")


# Backwards compatibility - ConsolePrinter as default
def print_metrics(metrics, org, repo, period):
    """Print metrics for a single repo (backwards compatibility)."""
    printer = ConsolePrinter()
    _print_single_repo_metrics(printer, metrics, org, repo, period)


def _print_single_repo_metrics(printer: Printer, metrics, org, repo, period):
    """Print metrics for a single repo."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title=f"Repo Metrics (last {period})")
    for col in [
        "Repo",
        "Pickup Time (h)",
        "Review Time (h)",
        "Cycle Time (h)",
        "PR Size",
        "Total PRs",
        "PRs/Week",
        "Reviews Given",
    ]:
        table.add_column(col)

    table.add_row(
        f"{org}/{repo}",
        f"{metrics['pickup_time']:.2f}",
        f"{metrics['review_time']:.2f}",
        f"{metrics['cycle_time']:.2f}",
        f"{metrics['pr_size']:.1f}",
        f"{metrics['pr_count']:.0f}",
        f"{metrics['prs_per_week']:.2f}",
        f"{metrics['reviews_given']:.0f}",
    )

    console.print("\n")
    console.print(table)

    dev_table = Table(title="Developer Metrics")
    for col in [
        "Dev",
        "Pickup Time (h)",
        "Review Time (h)",
        "Cycle Time (h)",
        "PR Size",
        "Total PRs",
        "PRs/Week",
        "Reviews Given",
    ]:
        dev_table.add_column(col)

    for dev, m in sorted(
        metrics["dev_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
    ):
        dev_table.add_row(
            dev,
            f"{m['pickup_time']:.2f}",
            f"{m['review_time']:.2f}",
            f"{m['cycle_time']:.2f}",
            f"{m['pr_size']:.1f}",
            f"{m['pr_count']:.0f}",
            f"{m['prs_per_week']:.2f}",
            f"{m['reviews_given']:.0f}",
        )

    console.print(dev_table)

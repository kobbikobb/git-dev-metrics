from pathlib import Path

from ..metrics.printer import (
    get_default_output_path,
)
from ..metrics.printer import (
    print_combined_metrics as _print_combined_metrics,
)
from ..metrics.printer import (
    print_stale_prs as _print_stale_prs,
)


def resolve_output_path(output: Path | None, period: str = "") -> Path:
    """Resolve output path from user input or return default with period encoded."""
    return output if output else get_default_output_path(period)


def print_metrics(metrics: dict, period: str, output_path: Path, date_range: str) -> None:
    """Print metrics to the specified output path."""
    _print_combined_metrics(metrics, period, output_path, date_range)


def print_stale_prs(stale_prs: list[dict], output_path: Path) -> None:
    """Print stale PRs to file."""
    _print_stale_prs(stale_prs, output_path)

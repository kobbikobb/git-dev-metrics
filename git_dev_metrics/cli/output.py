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


def resolve_output_path(output: Path | None) -> Path:
    """Resolve output path from user input or return default."""
    return output if output else get_default_output_path()


def print_metrics(metrics: dict, period: str, output_path: Path) -> None:
    """Print metrics to the specified output path."""
    import typer

    _print_combined_metrics(metrics, period, output_path)
    typer.secho(f"Results saved to {output_path}", fg=typer.colors.GREEN)


def print_stale_prs(stale_prs: list[dict], output_path: Path) -> None:
    """Print stale PRs to console and file."""
    import typer

    _print_stale_prs(stale_prs, output_path)
    typer.secho(f"Stale PRs saved to {output_path}", fg=typer.colors.YELLOW)

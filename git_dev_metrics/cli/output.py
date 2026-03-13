from pathlib import Path

from ..metrics.printer import CompositePrinter, get_default_output_path


def resolve_output_path(output: Path | None) -> Path:
    """Resolve output path from user input or return default."""
    return output if output else get_default_output_path()


def print_metrics(metrics: dict, period: str, output_path: Path) -> None:
    """Print metrics to the specified output path."""
    import typer

    CompositePrinter(output_path).print_combined_metrics(metrics, period)
    typer.secho(f"Results saved to {output_path}", fg=typer.colors.GREEN)


def print_stale_prs(stale_prs: list[dict], output_path: Path) -> None:
    """Print stale PRs to console and file."""
    import typer

    from ..metrics.printer import ConsoleStalePRPrinter, FileStalePRPrinter

    ConsoleStalePRPrinter().print_stale_prs(stale_prs)
    FileStalePRPrinter(output_path).print_stale_prs(stale_prs)
    typer.secho(f"Stale PRs saved to {output_path}", fg=typer.colors.YELLOW)

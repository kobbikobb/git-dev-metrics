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

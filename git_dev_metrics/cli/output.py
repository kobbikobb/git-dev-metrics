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
    """Append stale PRs to the output file."""
    import typer

    with open(output_path, "a") as f:
        f.write("\n# Stale PRs\n\n")
        f.write(f"Total stale PRs: {len(stale_prs)}\n\n")
        f.write("| PR | Title | Author | Age (hours) |\n")
        f.write("|---|---|---|---|\n")
        for pr in stale_prs:
            title = pr["title"][:50] + "..." if len(pr["title"]) > 50 else pr["title"]
            f.write(f"| #{pr['number']} | {title} | {pr['author']} | {pr['age_hours']} |\n")

    typer.secho(f"Stale PRs saved to {output_path}", fg=typer.colors.YELLOW)

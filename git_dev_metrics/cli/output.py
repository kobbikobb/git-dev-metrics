from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..metrics.printer import CompositePrinter, get_default_output_path


def resolve_output_path(output: Path | None) -> Path:
    """Resolve output path from user input or return default."""
    return output if output else get_default_output_path()


def print_metrics(metrics: dict, period: str, output_path: Path) -> None:
    """Print metrics to the specified output path."""
    CompositePrinter(output_path).print_combined_metrics(metrics, period)
    typer.secho(f"Results saved to {output_path}", fg=typer.colors.GREEN)


def print_bottlenecks(bottleneck_data: dict, output_path: Path) -> None:
    """Print bottleneck analysis to the output file."""
    aging = bottleneck_data.get("aging", {})
    bottlenecks = bottleneck_data.get("bottlenecks", {})

    # Append bottleneck section to the output file
    with open(output_path, "a") as f:
        f.write("\n# Bottleneck Analysis\n\n")

        # PR Aging summary
        f.write("## PR Aging Summary\n")
        f.write(f"- Open PRs: {aging.get('open_count', 0)}\n")
        f.write(f"- Stale PRs (> 7 days): {aging.get('stale_count', 0)}\n")
        f.write(f"- Average age: {aging.get('avg_age_hours', 0):.1f} hours\n\n")

        # Stale PRs table
        stale_prs = bottlenecks.get("stale_prs", [])
        if stale_prs:
            f.write("## Stale PRs (> 7 days)\n\n")
            f.write("| Repo | PR | Author | Age (hours) |\n")
            f.write("|---|---|---|---|\n")
            for pr in stale_prs:
                title = pr["title"][:40]
                line = (
                    f"| {pr['repo']} | #{pr['number']} | {pr['author']} | {pr['age_hours']:.1f} |\n"
                )
                f.write(line)
            f.write("\n")

        # Waiting for review
        waiting = bottlenecks.get("waiting_for_review", [])
        if waiting:
            f.write("## PRs Waiting for Review (> 48h)\n\n")
            f.write("| Repo | PR | Author | Waiting (hours) |\n")
            f.write("|---|---|---|---|\n")
            for pr in waiting:
                title = pr["title"][:40]
                line = f"| {pr['repo']} | #{pr['number']} | {pr['author']} | {pr['waiting_hours']:.1f} |\n"
                f.write(line)
            f.write("\n")

        # Overwhelmed reviewers
        overwhelmed = bottlenecks.get("overwhelmed_reviewers", [])
        if overwhelmed:
            f.write("## Overwhelmed Reviewers (>= 5 pending)\n\n")
            f.write("| Reviewer | Pending Reviews |\n")
            f.write("|---|---|\n")
            for r in overwhelmed:
                f.write(f"| {r['reviewer']} | {r['pending_count']} |\n")
            f.write("\n")

    # Console output
    console = Console()

    stale_count = aging.get("stale_count", 0)
    stale_prs = bottlenecks.get("stale_prs", [])

    aging_table = Table(title="PR Aging Summary")
    aging_table.add_column("Metric", style="cyan")
    aging_table.add_column("Value", style="magenta")
    aging_table.add_row("Open PRs", str(aging.get("open_count", 0)))
    aging_table.add_row("Stale PRs (> 7 days)", str(stale_count))
    aging_table.add_row("Avg age (hours)", f"{aging.get('avg_age_hours', 0):.1f}")
    console.print(aging_table)

    # Stale PRs table
    if stale_prs:
        display_count = min(10, len(stale_prs))
        title = (
            f"Oldest PRs ({display_count})"
            if stale_count <= display_count
            else f"Oldest PRs ({display_count} of {stale_count})"
        )
        stale_table = Table(title=title)
        stale_table.add_column("Repo", style="dim", width=25)
        stale_table.add_column("PR", style="cyan", width=6)
        stale_table.add_column("Author", style="yellow", width=12)
        stale_table.add_column("Age", style="red", width=8)
        for pr in stale_prs[:10]:
            stale_table.add_row(
                pr.get("repo", ""),
                f"#{pr['number']}",
                pr.get("author", ""),
                f"{pr['age_hours']:.0f}h",
            )
        console.print(stale_table)

    # Overwhelmed reviewers
    overwhelmed = bottlenecks.get("overwhelmed_reviewers", [])
    if overwhelmed:
        overwhelmed_count = len(overwhelmed)
        display_count = min(10, overwhelmed_count)
        title = (
            f"Overwhelmed ({display_count})"
            if overwhelmed_count <= display_count
            else f"Overwhelmed ({display_count} of {overwhelmed_count})"
        )
        overwhelmed_table = Table(title=title)
        overwhelmed_table.add_column("Reviewer", style="cyan", width=20)
        overwhelmed_table.add_column("Pending", style="red", width=8)
        for r in overwhelmed[:10]:
            overwhelmed_table.add_row(r["reviewer"], str(r["pending_count"]))
        console.print(overwhelmed_table)

    typer.secho(f"Bottleneck analysis saved to {output_path}", fg=typer.colors.GREEN)

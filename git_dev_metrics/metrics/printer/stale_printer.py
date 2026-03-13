from pathlib import Path


class ConsoleStalePRPrinter:
    """Print stale PRs to console using Rich."""

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Stale PRs (> 7 days)")
        table.add_column("Repo", style="dim")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Author", style="magenta")
        table.add_column("Age (h)", style="yellow", justify="right")

        for pr in stale_prs:
            title = pr["title"][:35] + "..." if len(pr["title"]) > 35 else pr["title"]
            table.add_row(
                pr.get("repo", ""),
                f"#{pr['number']}",
                title,
                pr["author"],
                f"{pr['age_hours']:.0f}",
            )

        console.print("\n")
        console.print(table)


class FileStalePRPrinter:
    """Print stale PRs to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        with open(self.output_path, "a") as f:
            f.write("\n# Stale PRs\n\n")
            f.write(f"Total stale PRs: {len(stale_prs)}\n\n")
            f.write("| Repo | PR | Title | Author | Age (hours) |\n")
            f.write("|---|---|---|---|---|\n")
            for pr in stale_prs:
                title = pr["title"][:40] + "..." if len(pr["title"]) > 40 else pr["title"]
                f.write(
                    f"| {pr.get('repo', '')} | #{pr['number']} | {title} | "
                    f"{pr['author']} | {pr['age_hours']:.0f} |\n"
                )

from pathlib import Path


class ConsoleStalePRPrinter:
    """Print stale PRs to console using Rich."""

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        total = len(stale_prs)
        avg_age_days = 0.0
        if stale_prs:
            avg_age_days = sum(pr["age_days"] for pr in stale_prs) / total

        console.print("\n")
        if total > 0:
            console.print(f"[bold]Stale PRs: {total} | Avg Age: {avg_age_days:.1f} days[/bold]\n")

        table = Table(title="Stale PRs (> 7 days)")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Repo", style="dim")
        table.add_column("Author", style="magenta")
        table.add_column("Age (d)", style="yellow", justify="right")

        for pr in stale_prs:
            title = pr["title"][:35] + "..." if len(pr["title"]) > 35 else pr["title"]
            table.add_row(
                f"[link={pr['url']}]#{pr['number']}[/link]",
                title,
                pr.get("repo", ""),
                pr["author"],
                f"{pr['age_days']:.1f}",
            )

        console.print(table)


class FileStalePRPrinter:
    """Print stale PRs to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        total = len(stale_prs)
        avg_age_days = 0.0
        if stale_prs:
            avg_age_days = sum(pr["age_days"] for pr in stale_prs) / total

        with open(self.output_path, "a") as f:
            f.write("\n# Stale PRs\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age_days:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Author | Age (days) |\n")
            f.write("|---|---|---|---|---|\n")
            for pr in stale_prs:
                title = pr["title"][:40] + "..." if len(pr["title"]) > 40 else pr["title"]
                f.write(
                    f"| [#{pr['number']}]({pr['url']}) | {title} | {pr.get('repo', '')} | "
                    f"{pr['author']} | {pr['age_days']:.1f} |\n"
                )

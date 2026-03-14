from pathlib import Path


def _calculate_summary(prs: list[dict]) -> tuple[int, float]:
    """Calculate total count and average age in days."""
    total = len(prs)
    avg_age = sum(pr["age_days"] for pr in prs) / total if prs else 0.0
    return total, round(avg_age, 1)


def _truncate(text: str, length: int) -> str:
    """Truncate text to length with ellipsis."""
    return text[:length] + "..." if len(text) > length else text


TITLE_CONSOLE_LENGTH = 35
TITLE_FILE_LENGTH = 40
REVIEWERS_CONSOLE_LENGTH = 25
REVIEWERS_FILE_LENGTH = 35


class ConsoleStalePRPrinter:
    """Print stale PRs to console using Rich."""

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        if not stale_prs:
            return

        console = Console()
        total, avg_age = _calculate_summary(stale_prs)

        console.print("\n")
        console.print(f"[bold]Stale PRs: {total} | Avg Age: {avg_age:.1f} days[/bold]\n")

        table = Table(title="Stale PRs (> 7 days)")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Repo", style="dim")
        table.add_column("Author", style="magenta")
        table.add_column("Age (d)", style="yellow", justify="right")

        for pr in stale_prs:
            table.add_row(
                f"[link={pr['url']}]#{pr['number']}[/link]",
                _truncate(pr["title"], TITLE_CONSOLE_LENGTH),
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
        if not stale_prs:
            return

        total, avg_age = _calculate_summary(stale_prs)

        with open(self.output_path, "a") as f:
            f.write("\n# Stale PRs\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Author | Age (days) |\n")
            f.write("|---|---|---|---|---|\n")
            for pr in stale_prs:
                row = (
                    f"| [#{pr['number']}]({pr['url']}) | "
                    f"{_truncate(pr['title'], TITLE_FILE_LENGTH)} | "
                    f"{pr.get('repo', '')} | {pr['author']} | {pr['age_days']:.1f} |\n"
                )
                f.write(row)

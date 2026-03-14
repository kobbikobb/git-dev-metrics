from pathlib import Path

MAX_STALE_PRS_DISPLAY = 10


def _calculate_summary(prs: list[dict]) -> tuple[int, float]:
    """Calculate total count and average age in days."""
    total = len(prs)
    avg_age = sum(pr["age_days"] for pr in prs) / total if prs else 0.0
    return total, round(avg_age, 1)


def _truncate(text: str, length: int) -> str:
    """Truncate text to length with ellipsis."""
    return text[:length] + "..." if len(text) > length else text


def _check_mark(value: bool) -> str:
    """Return check mark or cross mark for boolean."""
    return "✓" if value else "✗"


TITLE_CONSOLE_LENGTH = 30
TITLE_FILE_LENGTH = 35


class ConsoleStalePRPrinter:
    """Print stale PRs to console using Rich."""

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        if not stale_prs:
            return

        console = Console()
        total, avg_age = _calculate_summary(stale_prs)
        display_prs = stale_prs[:MAX_STALE_PRS_DISPLAY]

        console.print("\n")
        if total > MAX_STALE_PRS_DISPLAY:
            console.print(
                f"[bold]Stale PRs: {total} (showing {MAX_STALE_PRS_DISPLAY}) | Avg Age: "
                f"{avg_age:.1f} days[/bold]\n"
            )
        else:
            console.print(f"[bold]Stale PRs: {total} | Avg Age: {avg_age:.1f} days[/bold]\n")

        table = Table(title="Stale PRs (> 7 days)")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Repo", style="dim")
        table.add_column("Author", style="magenta")
        table.add_column("Draft", style="cyan", justify="center")
        table.add_column("Approved", style="green", justify="center")
        table.add_column("Age (d)", style="yellow", justify="right")

        for pr in display_prs:
            table.add_row(
                f"[link={pr['url']}]#{pr['number']}[/link]",
                _truncate(pr["title"], TITLE_CONSOLE_LENGTH),
                pr.get("repo", ""),
                pr["author"],
                _check_mark(pr.get("is_draft", False)),
                _check_mark(pr.get("is_approved", False)),
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
        display_prs = stale_prs[:MAX_STALE_PRS_DISPLAY]

        with open(self.output_path, "a") as f:
            f.write("\n# Stale PRs\n\n")
            if total > MAX_STALE_PRS_DISPLAY:
                f.write(
                    f"**Total: {total} (showing {MAX_STALE_PRS_DISPLAY}) | Avg Age: "
                    f"{avg_age:.1f} days**\n\n"
                )
            else:
                f.write(f"**Total: {total} | Avg Age: {avg_age:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Author | Draft | Approved | Age (days) |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for pr in display_prs:
                row = (
                    f"| [#{pr['number']}]({pr['url']}) | "
                    f"{_truncate(pr['title'], TITLE_FILE_LENGTH)} | "
                    f"{pr.get('repo', '')} | {pr['author']} | "
                    f"{_check_mark(pr.get('is_draft', False))} | "
                    f"{_check_mark(pr.get('is_approved', False))} | "
                    f"{pr['age_days']:.1f} |\n"
                )
                f.write(row)

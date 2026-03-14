from pathlib import Path

from .stale_printer import _calculate_summary, _truncate

TITLE_CONSOLE_LENGTH = 35
TITLE_FILE_LENGTH = 40
REVIEWERS_CONSOLE_LENGTH = 25
REVIEWERS_FILE_LENGTH = 35


class ConsoleBottleneckPrinter:
    """Print bottleneck PRs to console using Rich."""

    def print_draft_prs(self, prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        if not prs:
            return

        console = Console()
        total, avg_age = _calculate_summary(prs)

        console.print("\n")
        console.print(f"[bold]Draft PRs: {total} | Avg Age: {avg_age:.1f} days[/bold]\n")

        table = Table(title="Draft PRs")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Repo", style="dim")
        table.add_column("Author", style="magenta")
        table.add_column("Age (d)", style="yellow", justify="right")

        for pr in prs:
            table.add_row(
                f"[link={pr['url']}]#{pr['number']}[/link]",
                _truncate(pr["title"], TITLE_CONSOLE_LENGTH),
                pr.get("repo", ""),
                pr["author"],
                f"{pr['age_days']:.1f}",
            )

        console.print(table)

    def print_awaiting_review_prs(self, prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        if not prs:
            return

        console = Console()
        total, avg_age = _calculate_summary(prs)

        console.print("\n")
        console.print(f"[bold]Awaiting Review: {total} | Avg Age: {avg_age:.1f} days[/bold]\n")

        table = Table(title="PRs Awaiting Review")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Repo", style="dim")
        table.add_column("Reviewers", style="blue")
        table.add_column("Age (d)", style="yellow", justify="right")

        for pr in prs:
            reviewers = ", ".join(pr.get("review_requests", []))
            table.add_row(
                f"[link={pr['url']}]#{pr['number']}[/link]",
                _truncate(pr["title"], TITLE_CONSOLE_LENGTH - 5),
                pr.get("repo", ""),
                reviewers[:REVIEWERS_CONSOLE_LENGTH],
                f"{pr['age_days']:.1f}",
            )

        console.print(table)


class FileBottleneckPrinter:
    """Print bottleneck PRs to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_draft_prs(self, prs: list[dict]) -> None:
        if not prs:
            return

        total, avg_age = _calculate_summary(prs)

        with open(self.output_path, "a") as f:
            f.write("\n# Draft PRs\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Author | Age (days) |\n")
            f.write("|---|---|---|---|---|\n")
            for pr in prs:
                row = (
                    f"| [#{pr['number']}]({pr['url']}) | "
                    f"{_truncate(pr['title'], TITLE_FILE_LENGTH)} | "
                    f"{pr.get('repo', '')} | {pr['author']} | {pr['age_days']:.1f} |\n"
                )
                f.write(row)

    def print_awaiting_review_prs(self, prs: list[dict]) -> None:
        if not prs:
            return

        total, avg_age = _calculate_summary(prs)

        with open(self.output_path, "a") as f:
            f.write("\n# PRs Awaiting Review\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Reviewers | Age (days) |\n")
            f.write("|---|---|---|---|---|\n")
            for pr in prs:
                reviewers = ", ".join(pr.get("review_requests", []))
                row = (
                    f"| [#{pr['number']}]({pr['url']}) | "
                    f"{_truncate(pr['title'], TITLE_FILE_LENGTH - 5)} | "
                    f"{pr.get('repo', '')} | {reviewers[:REVIEWERS_FILE_LENGTH]} | "
                    f"{pr['age_days']:.1f} |\n"
                )
                f.write(row)

from pathlib import Path


class ConsoleBottleneckPrinter:
    """Print bottleneck PRs to console using Rich."""

    def print_draft_prs(self, prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        total = len(prs)
        avg_age_days = 0.0
        if prs:
            avg_age_days = sum(pr["age_days"] for pr in prs) / total

        console.print("\n")
        if total > 0:
            console.print(f"[bold]Draft PRs: {total} | Avg Age: {avg_age_days:.1f} days[/bold]\n")

        table = Table(title="Draft PRs")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Repo", style="dim")
        table.add_column("Author", style="magenta")
        table.add_column("Age (d)", style="yellow", justify="right")

        for pr in prs:
            title = pr["title"][:35] + "..." if len(pr["title"]) > 35 else pr["title"]
            table.add_row(
                f"[link={pr['url']}]#{pr['number']}[/link]",
                title,
                pr.get("repo", ""),
                pr["author"],
                f"{pr['age_days']:.1f}",
            )

        console.print(table)

    def print_awaiting_review_prs(self, prs: list[dict]) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        total = len(prs)
        avg_age_days = 0.0
        if prs:
            avg_age_days = sum(pr["age_days"] for pr in prs) / total

        console.print("\n")
        if total > 0:
            console.print(
                f"[bold]Awaiting Review: {total} | Avg Age: {avg_age_days:.1f} days[/bold]\n"
            )

        table = Table(title="PRs Awaiting Review")
        table.add_column("PR", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Repo", style="dim")
        table.add_column("Reviewers", style="blue")
        table.add_column("Age (d)", style="yellow", justify="right")

        for pr in prs:
            title = pr["title"][:30] + "..." if len(pr["title"]) > 30 else pr["title"]
            reviewers = ", ".join(pr.get("review_requests", []))
            table.add_row(
                f"[link={pr['url']}]#{pr['number']}[/link]",
                title,
                pr.get("repo", ""),
                reviewers[:25],
                f"{pr['age_days']:.1f}",
            )

        console.print(table)


class FileBottleneckPrinter:
    """Print bottleneck PRs to markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def print_draft_prs(self, prs: list[dict]) -> None:
        total = len(prs)
        avg_age_days = 0.0
        if prs:
            avg_age_days = sum(pr["age_days"] for pr in prs) / total

        with open(self.output_path, "a") as f:
            f.write("\n# Draft PRs\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age_days:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Author | Age (days) |\n")
            f.write("|---|---|---|---|---|\n")
            for pr in prs:
                title = pr["title"][:40] + "..." if len(pr["title"]) > 40 else pr["title"]
                f.write(
                    f"| [#{pr['number']}]({pr['url']}) | {title} | {pr.get('repo', '')} | "
                    f"{pr['author']} | {pr['age_days']:.1f} |\n"
                )

    def print_awaiting_review_prs(self, prs: list[dict]) -> None:
        total = len(prs)
        avg_age_days = 0.0
        if prs:
            avg_age_days = sum(pr["age_days"] for pr in prs) / total

        with open(self.output_path, "a") as f:
            f.write("\n# PRs Awaiting Review\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age_days:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Reviewers | Age (days) |\n")
            f.write("|---|---|---|---|---|\n")
            for pr in prs:
                title = pr["title"][:35] + "..." if len(pr["title"]) > 35 else pr["title"]
                reviewers = ", ".join(pr.get("review_requests", []))
                f.write(
                    f"| [#{pr['number']}]({pr['url']}) | {title} | {pr.get('repo', '')} | "
                    f"{reviewers} | {pr['age_days']:.1f} |\n"
                )

from pathlib import Path


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


TITLE_FILE_LENGTH = 60


def _stale_path(output_path: Path) -> Path:
    """Sibling file with `_stale` appended to the stem."""
    return output_path.with_name(f"{output_path.stem}_stale{output_path.suffix}")


class FileStalePRPrinter:
    """Print stale PRs to a dedicated markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = _stale_path(output_path)

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        if not stale_prs:
            return

        total, avg_age = _calculate_summary(stale_prs)
        sorted_prs = sorted(stale_prs, key=lambda pr: pr["age_days"], reverse=True)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w") as f:
            f.write("# Stale PRs\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Author | Draft | Approved | Age (days) |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for pr in sorted_prs:
                row = (
                    f"| [#{pr['number']}]({pr['url']}) | "
                    f"{_truncate(pr['title'], TITLE_FILE_LENGTH)} | "
                    f"{pr.get('repo', '')} | {pr['author']} | "
                    f"{_check_mark(pr.get('is_draft', False))} | "
                    f"{_check_mark(pr.get('is_approved', False))} | "
                    f"{pr['age_days']:.1f} |\n"
                )
                f.write(row)

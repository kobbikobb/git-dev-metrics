from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..calculator import summarize_stale_prs

TITLE_FILE_LENGTH = 60

_ENV: Environment | None = None


def _get_env() -> Environment:
    global _ENV
    if _ENV is None:
        _ENV = Environment(
            loader=PackageLoader("git_dev_metrics.metrics.printer", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
    return _ENV


class FileStaleHtmlPrinter:
    """Render a self-contained stale-PR HTML report."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, stale_prs: list[dict]) -> None:
        total, avg_age = summarize_stale_prs(stale_prs)
        html = (
            _get_env()
            .get_template("stale.html")
            .render(total=total, avg_age=avg_age, prs=stale_prs)
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


def _truncate(text: str, length: int) -> str:
    return text[:length] + "..." if len(text) > length else text


def _check_mark(value: bool) -> str:
    return "✓" if value else "✗"


def _stale_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}_stale{output_path.suffix}")


class FileStalePRPrinter:
    """Print stale PRs to a dedicated markdown file."""

    def __init__(self, output_path: Path):
        self.output_path = _stale_path(output_path)

    def print_stale_prs(self, stale_prs: list[dict]) -> None:
        if not stale_prs:
            return

        total, avg_age = summarize_stale_prs(stale_prs)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w") as f:
            f.write("# Stale PRs\n\n")
            f.write(f"**Total: {total} | Avg Age: {avg_age:.1f} days**\n\n")
            f.write("| PR | Title | Repo | Author | Draft | Approved | Age (days) |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for pr in stale_prs:
                row = (
                    f"| [#{pr['number']}]({pr['url']}) | "
                    f"{_truncate(pr['title'], TITLE_FILE_LENGTH)} | "
                    f"{pr.get('repo', '')} | {pr['author']} | "
                    f"{_check_mark(pr.get('is_draft', False))} | "
                    f"{_check_mark(pr.get('is_approved', False))} | "
                    f"{pr['age_days']:.1f} |\n"
                )
                f.write(row)

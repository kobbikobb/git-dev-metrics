from pathlib import Path

from ..calculator import summarize_stale_prs
from ._html_templates import render_template


class FileStaleHtmlPrinter:
    """Render a self-contained stale-PR HTML view."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, stale_prs: list[dict]) -> None:
        total, avg_age = summarize_stale_prs(stale_prs)
        html = render_template("stale.html", total=total, avg_age=avg_age, prs=stale_prs)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)

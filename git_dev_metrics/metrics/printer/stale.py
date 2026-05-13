from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..calculator import summarize_stale_prs

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
    """Render a self-contained stale-PR HTML view."""

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

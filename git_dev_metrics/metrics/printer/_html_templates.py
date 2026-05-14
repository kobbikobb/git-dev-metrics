from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

_ENV: Environment | None = None


def render_template(template_name: str, **context: Any) -> str:
    global _ENV
    if _ENV is None:
        _ENV = Environment(
            loader=PackageLoader("git_dev_metrics.metrics.printer", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
    template = _ENV.get_template(template_name)
    return template.render(context)

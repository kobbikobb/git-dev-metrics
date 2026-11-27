from collections.abc import Set
from pathlib import Path

from ..lang_calculator import LangDataset
from ._html_templates import render_template


class FileLangPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(
        self, dataset: LangDataset, period_range: str, *, hidden_logins: Set[str] = frozenset()
    ) -> None:
        devs = [dev for dev in dataset.devs if dev.lower() not in hidden_logins]
        html = render_template(
            "lang.html",
            period_range=period_range,
            devs=devs,
            langs=dataset.langs,
            dev_langs={dev: dict(dataset.dev_langs[dev]) for dev in devs},
            team_langs=dataset.team_langs,
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileLangPrinter"]

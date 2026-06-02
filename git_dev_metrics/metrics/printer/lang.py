from pathlib import Path

from ..lang_calculator import LangDataset
from ._html_templates import render_template


class FileLangPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, dataset: LangDataset, period_range: str) -> None:
        html = render_template(
            "lang.html",
            period_range=period_range,
            devs=dataset.devs,
            langs=dataset.langs,
            dev_langs={k: dict(v) for k, v in dataset.dev_langs.items()},
            team_langs=dataset.team_langs,
        )
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)


__all__ = ["FileLangPrinter"]

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from ..constants import is_bot_login
from ._rows import DeveloperSeries, developer_series

LANG_MAP: dict[str, str] = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C",
    ".cs": "C#",
    ".scala": "Scala",
    ".tf": "Terraform",
    ".tfvars": "Terraform",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".md": "Documentation",
    ".rst": "Documentation",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".dockerfile": "Docker",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".less": "CSS",
    ".xml": "XML",
    ".gradle": "Groovy",
    ".proto": "Protobuf",
}

_BASENAME_MAP: dict[str, str] = {
    "Dockerfile": "Docker",
    "Makefile": "Make",
    "CMakeLists.txt": "Make",
    "compose.yml": "YAML",
    "compose.yaml": "YAML",
}


def _classify(path: str) -> str:
    for basename, lang in _BASENAME_MAP.items():
        if path.endswith(basename):
            return lang
    _, _, ext = path.rpartition(".")
    return LANG_MAP.get(f".{ext}", "Other")


@dataclass(frozen=True)
class LangDataset:
    devs: list[DeveloperSeries[dict[str, int]]]
    team_langs: dict[str, int]


def build_lang_dataset(prs: list[dict], display_name: Callable[[str], str | None]) -> LangDataset:
    by_dev: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    team: dict[str, int] = defaultdict(int)
    for pr in prs:
        login = pr.get("user", {}).get("login", "")
        if is_bot_login(login):
            continue
        for lang in {_classify(f.get("path", "")) for f in pr.get("files", [])}:
            by_dev[login][lang] += 1
            team[lang] += 1
    return LangDataset(devs=developer_series(by_dev, display_name), team_langs=dict(team))

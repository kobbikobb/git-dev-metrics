from collections import defaultdict
from dataclasses import dataclass, field

from ..constants import is_bot_login

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


@dataclass
class LangDataset:
    dev_langs: dict[str, dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int))
    )
    devs: list[str] = field(default_factory=list)
    langs: list[str] = field(default_factory=list)

    @property
    def team_langs(self) -> dict[str, int]:
        out: dict[str, int] = defaultdict(int)
        for dev_data in self.dev_langs.values():
            for lang, count in dev_data.items():
                out[lang] += count
        return dict(out)

    def _finalize(self) -> None:
        self.devs = sorted(self.dev_langs)
        all_langs: set[str] = set()
        for data in self.dev_langs.values():
            all_langs.update(data)
        self.langs = sorted(all_langs)


def build_lang_dataset(prs: list[dict]) -> LangDataset:
    ds = LangDataset()
    for pr in prs:
        login = pr.get("user", {}).get("login", "")
        if is_bot_login(login):
            continue
        seen: set[str] = set()
        for f in pr.get("files", []):
            lang = _classify(f.get("path", ""))
            if lang not in seen:
                seen.add(lang)
                ds.dev_langs[login][lang] += 1
    ds._finalize()
    return ds

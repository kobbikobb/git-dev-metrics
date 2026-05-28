from collections import defaultdict
from dataclasses import dataclass, field

from ..constants import is_bot_login

SKILL_MAP: dict[str, str] = {
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
    for basename, skill in _BASENAME_MAP.items():
        if path.endswith(basename):
            return skill
    _, _, ext = path.rpartition(".")
    return SKILL_MAP.get(f".{ext}", "Other")


@dataclass
class SkillDataset:
    dev_skills: dict[str, dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(int))
    )
    devs: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)

    @property
    def team_skills(self) -> dict[str, int]:
        out: dict[str, int] = defaultdict(int)
        for dev_data in self.dev_skills.values():
            for skill, count in dev_data.items():
                out[skill] += count
        return dict(out)

    def _finalize(self) -> None:
        self.devs = sorted(self.dev_skills)
        all_skills: set[str] = set()
        for data in self.dev_skills.values():
            all_skills.update(data)
        self.skills = sorted(all_skills)


def build_skill_dataset(prs: list[dict]) -> SkillDataset:
    ds = SkillDataset()
    for pr in prs:
        login = pr.get("user", {}).get("login", "")
        if is_bot_login(login):
            continue
        seen: set[str] = set()
        for f in pr.get("files", []):
            skill = _classify(f.get("path", ""))
            if skill not in seen:
                seen.add(skill)
                ds.dev_skills[login][skill] += 1
    ds._finalize()
    return ds

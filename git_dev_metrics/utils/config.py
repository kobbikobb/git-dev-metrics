import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config"
CONFIG_FILE = CONFIG_DIR / "git-dev-metrics.json"


def load_last_org() -> str | None:
    """Load the last used organization from config file."""
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
        return data.get("last_org")
    return None


def save_last_org(org: str) -> None:
    """Save the organization to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
    data["last_org"] = org
    CONFIG_FILE.write_text(json.dumps(data, indent=2))

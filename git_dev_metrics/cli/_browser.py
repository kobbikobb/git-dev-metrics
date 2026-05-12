import webbrowser
from pathlib import Path


def open_in_browser(path: Path) -> None:
    webbrowser.open(path.resolve().as_uri())

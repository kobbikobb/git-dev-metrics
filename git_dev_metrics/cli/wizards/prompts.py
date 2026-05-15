import questionary
from questionary import Style

_STYLE = Style([("highlighted", "fg:#00b4d8 bold"), ("selected", "fg:#90e0ef")])


def prompt_org_name(default: str | None = None) -> str | None:
    """Prompt user to enter an organization name. Returns None for empty/orgless."""
    selected = questionary.text(
        "Enter organization name (leave empty for personal repos):",
        default=default or "",
        style=_STYLE,
    ).ask()

    return selected if selected else None


def prompt_repo_selection(repos: dict[str, str]) -> list[str]:
    """Multi-select repos. `repos` maps full_name to visibility. All checked by default."""
    choices = [
        questionary.Choice(title=f"{name} ({visibility})", value=name, checked=True)
        for name, visibility in repos.items()
    ]
    selected = questionary.checkbox(
        "Select repositories to include:", choices=choices, style=_STYLE
    ).ask()
    return selected or []

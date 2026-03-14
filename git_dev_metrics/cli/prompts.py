import questionary
from questionary import Style

from ..models import GitHubOrganization

PERIOD_OPTIONS = [
    ("Last 7 days", "7d"),
    ("Last 14 days", "14d"),
    ("Last 30 days", "30d"),
    ("Last 60 days", "60d"),
    ("Last 90 days", "90d"),
]


def prompt_period_selection(default: str | None = None) -> str:
    """Prompt user to select the time period."""
    choices = [questionary.Choice(title=title, value=value) for title, value in PERIOD_OPTIONS]

    custom_style = Style(
        [
            ("highlighted", "fg:#00b4d8 bold"),
            ("selected", "fg:#90e0ef"),
        ]
    )

    selected = questionary.select(
        "Select time period:",
        choices=choices,
        default=default or "30d",
        style=custom_style,
    ).ask()

    return selected or default or "30d"


def prompt_org_selection(orgs: list[GitHubOrganization], default: str | None = None) -> str:
    """Prompt user to select an organization."""
    if not orgs:
        raise questionary.ValidationError(message="No organizations found for this token")

    choices = [
        questionary.Choice(
            title=org.get("name", org["login"]) or org["login"],
            value=org["login"],
        )
        for org in orgs
    ]

    custom_style = Style(
        [
            ("highlighted", "fg:#00b4d8 bold"),
            ("selected", "fg:#90e0ef"),
        ]
    )

    selected = questionary.select(
        "Select organization:",
        choices=choices,
        default=default,
        style=custom_style,
    ).ask()

    if not selected:
        selected = orgs[0]["login"]

    return selected


def prompt_repo_selection(repos: dict[str, str]) -> list[str]:
    choices = [
        questionary.Choice(
            title=f"{name} ({visibility})",
            value=name,
            checked=True,  # all selected by default
        )
        for name, visibility in repos.items()
    ]

    custom_style = Style(
        [
            ("highlighted", "fg:#00b4d8 bold"),  # cursor row
            ("selected", "fg:#90e0ef"),  # checked items
        ]
    )

    selected = questionary.checkbox(
        "Select repositories to include:", choices=choices, style=custom_style
    ).ask()

    return selected or list(repos.keys())  # fallback if user cancels

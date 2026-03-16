import questionary
from questionary import Style

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


def prompt_org_name(default: str | None = None) -> str | None:
    """Prompt user to enter an organization name. Returns None for empty/orgless."""
    custom_style = Style(
        [
            ("highlighted", "fg:#00b4d8 bold"),
            ("selected", "fg:#90e0ef"),
        ]
    )

    selected = questionary.text(
        "Enter organization name (leave empty for personal repos):",
        default=default or "",
        style=custom_style,
    ).ask()

    return selected if selected else None


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

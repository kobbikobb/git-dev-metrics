from pathlib import Path

import click
import questionary
from questionary import Style

MAX_RESULT_FILES = 10

PERIOD_OPTIONS = [
    ("Last 7 days", "7d"),
    ("Last 14 days", "14d"),
    ("Last 30 days", "30d"),
    ("Last 60 days", "60d"),
    ("Last 90 days", "90d"),
    ("Last month (calendar)", "last_month"),
]


def prompt_period_selection(default: str | None = None) -> str:
    """Prompt user to select the time period."""
    valid_values = {value for _, value in PERIOD_OPTIONS}
    default = default if default in valid_values else "30d"

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
        default=default,
        style=custom_style,
    ).ask()

    return selected or default


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


def prompt_open_result(default_path: Path) -> None:
    """List recent result files, open the chosen one in the default app."""
    results_dir = default_path.parent
    files = sorted(
        [*results_dir.glob("metrics_*.html"), *results_dir.glob("metrics_*.md")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:MAX_RESULT_FILES]
    if not files:
        return

    choices = [questionary.Choice(title=f.name, value=f) for f in files]
    choices.append(questionary.Choice(title="(skip)", value=False))

    selected = questionary.select(
        "Open a result file:",
        choices=choices,
        default=choices[0],
    ).ask()

    if not selected:
        return
    click.launch(str(selected))

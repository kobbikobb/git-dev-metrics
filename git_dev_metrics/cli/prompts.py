import re
from datetime import UTC, datetime
from pathlib import Path

import click
import questionary
from questionary import Style

MAX_RESULT_FILES = 10

PICK_MONTH_SENTINEL = "__pick_month__"
CUSTOM_MONTH_SENTINEL = "__custom_month__"

PERIOD_OPTIONS = [
    ("Last 7 days", "7d"),
    ("Last 14 days", "14d"),
    ("Last 30 days", "30d"),
    ("Last 60 days", "60d"),
    ("Last 90 days", "90d"),
    ("Last month (calendar)", "last_month"),
    ("Pick a month…", PICK_MONTH_SENTINEL),
]

_YEAR_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _last_six_months(now: datetime) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    year, month = now.year, now.month
    for _ in range(6):
        label = datetime(year, month, 1).strftime("%B %Y")
        out.append((label, f"{year:04d}-{month:02d}"))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return out


def _validate_year_month(text: str) -> bool | str:
    return True if _YEAR_MONTH_RE.match(text) else "Use format YYYY-MM (e.g. 2026-03)"


def prompt_month_selection() -> str | None:
    """Sub-prompt: last 6 calendar months newest-first, plus custom YYYY-MM."""
    custom_style = Style(
        [
            ("highlighted", "fg:#00b4d8 bold"),
            ("selected", "fg:#90e0ef"),
        ]
    )

    months = _last_six_months(datetime.now(UTC))
    choices = [questionary.Choice(title=title, value=value) for title, value in months]
    choices.append(questionary.Choice(title="Custom (YYYY-MM)…", value=CUSTOM_MONTH_SENTINEL))

    selected = questionary.select(
        "Select month:",
        choices=choices,
        style=custom_style,
    ).ask()

    if selected is None:
        return None
    if selected != CUSTOM_MONTH_SENTINEL:
        return selected

    return questionary.text(
        "Enter year-month (YYYY-MM):",
        validate=_validate_year_month,
        style=custom_style,
    ).ask()


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

    if selected == PICK_MONTH_SENTINEL:
        return prompt_month_selection() or default

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
        (p for p in results_dir.glob("metrics_*") if p.suffix in {".md", ".html"}),
        key=lambda p: (p.stat().st_mtime, p.suffix),
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

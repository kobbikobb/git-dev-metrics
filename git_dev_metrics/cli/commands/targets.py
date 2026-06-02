from pathlib import Path

import typer

from ...cache import delete_target, get_targets, set_target

TARGET_KEYS: dict[str, str] = {
    "cycle_time_max": "Max cycle time (hours)",
    "pickup_time_max": "Max pickup time (hours)",
    "review_time_max": "Max review time (hours)",
    "health_min": "Min health score",
    "prs_per_week_min": "Min PRs/week",
    "stale_threshold_days": "Stale threshold (days)",
    "stale_max_count": "Max stale PR count",
    "stale_max_avg_age_days": "Max average stale age (days)",
    "stale_max_pr_age_days": "Max PR age (days)",
}


def targets(
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Set performance targets for team metrics."""
    current = get_targets(db_path=db)
    typer.echo("Enter a target value for each metric (blank keeps current, 'x' clears):")

    for key, label in TARGET_KEYS.items():
        existing = current.get(key)
        hint = f" [{existing}]" if existing is not None else ""
        val = typer.prompt(f"  {label}{hint}", default="", show_default=False, prompt_suffix="> ")

        if val == "x":
            if existing is not None:
                delete_target(key, db_path=db)
        elif val:
            try:
                parsed = float(val)
            except ValueError:
                typer.secho(f"  Invalid number: {val}", fg=typer.colors.RED, err=True)
                continue
            set_target(key, parsed, db_path=db)
            current[key] = parsed

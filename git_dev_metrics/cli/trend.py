from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import questionary
import typer
from questionary import Style

from ..cache import list_synced_months, load_all_repos_by_month
from ..metrics.printer.trend import FileTrendPrinter
from ..metrics.trend_calculator import build_trend_dataset
from ..utils.date_utils import month_iter
from ._browser import open_in_browser
from ._month_arg import parse_month_arg

YearMonth = tuple[int, int]

_STYLE = Style([("highlighted", "fg:#00b4d8 bold"), ("selected", "fg:#90e0ef")])


def _default_output(from_ym: YearMonth, to_ym: YearMonth) -> Path:
    return Path(
        f"./metrics_results/trend_"
        f"{from_ym[0]:04d}-{from_ym[1]:02d}_{to_ym[0]:04d}-{to_ym[1]:02d}.html"
    )


def _perform_trend(
    from_ym: YearMonth,
    to_ym: YearMonth,
    output: Path | None,
    db_path: Path | None,
) -> None:
    """Validate range, aggregate PRs across every cached repo, render HTML, open browser."""
    if to_ym < from_ym:
        typer.secho("--to must be >= --from.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    months = month_iter(from_ym, to_ym)
    prs_per_month = load_all_repos_by_month(months, db_path=db_path)
    if not any(prs_per_month.values()):
        typer.secho(
            "No synced data for selected range. Run pull first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    dataset = build_trend_dataset(months, prs_per_month)
    out_path = output or _default_output(from_ym, to_ym)
    FileTrendPrinter(out_path).render(dataset)
    typer.echo(f"Trend written to {out_path}.")
    open_in_browser(out_path)


def _month_choices(months: list[YearMonth]) -> list[questionary.Choice]:
    return [
        questionary.Choice(title=datetime(y, m, 1).strftime("%B %Y"), value=(y, m))
        for y, m in months
    ]


def _prompt_from(months: list[YearMonth]) -> YearMonth | None:
    return questionary.select(
        "From month:", choices=_month_choices(list(reversed(months))), style=_STYLE
    ).ask()


def _prompt_to(months: list[YearMonth]) -> YearMonth | None:
    return questionary.select(
        "To month:", choices=_month_choices(list(reversed(months))), style=_STYLE
    ).ask()


def _trend_wizard(
    db_path: Path | None = None,
    *,
    ask_from: Callable[[list[YearMonth]], YearMonth | None] = _prompt_from,
    ask_to: Callable[[list[YearMonth]], YearMonth | None] = _prompt_to,
) -> None:
    """Pick from/to months across the union of synced months; render aggregated trend HTML."""
    synced = list_synced_months(db_path=db_path)
    if not synced:
        typer.secho("No synced months — run pull first.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    months = sorted({(y, m) for _, _, y, m in synced})
    from_ym = ask_from(months)
    if from_ym is None:
        raise typer.Exit(code=1)
    to_candidates = [ym for ym in months if ym >= from_ym]
    to_ym = ask_to(to_candidates)
    if to_ym is None:
        raise typer.Exit(code=1)

    _perform_trend(from_ym, to_ym, output=None, db_path=db_path)


def trend(
    from_: str | None = typer.Option(None, "--from", help="Start month, YYYY-MM"),
    to: str | None = typer.Option(None, "--to", help="End month, YYYY-MM"),
    output: Path | None = typer.Option(None, "--output", help="Output HTML path"),
    db: Path | None = typer.Option(None, "--db", help="Override cache database path"),
) -> None:
    """Render a multi-month trend HTML aggregated across all cached repos."""
    if from_ is None and to is None:
        _trend_wizard(db_path=db)
        return

    if from_ is None or to is None:
        typer.secho(
            "Provide both --from and --to, or neither (for the wizard).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    from_ym = parse_month_arg(from_, "--from")
    to_ym = parse_month_arg(to, "--to")
    _perform_trend(from_ym, to_ym, output=output, db_path=db)

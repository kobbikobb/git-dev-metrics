from collections.abc import Callable, Iterator
from contextlib import contextmanager, nullcontext
from datetime import timedelta
from math import ceil
from pathlib import Path
from time import monotonic

import requests
import typer
from rich.console import Console
from rich.live import Live

from ...cache import open_connection
from ...classification import DEFAULT_MODEL, classify_pending
from .._options import DB_OPTION


@contextmanager
def _timed_progress(
    clock: Callable[[], float] = monotonic,
) -> Iterator[Callable[[int, int], None]]:
    console = Console(stderr=True)
    started = clock()
    count = ""
    eta = "estimating"

    def line() -> str:
        elapsed = timedelta(seconds=int(clock() - started))
        return f"{count} | elapsed {elapsed} | time left {eta}" if count else ""

    live = Live(console=console, get_renderable=line, refresh_per_second=1)
    with live if console.is_terminal else nullcontext():

        def update(done: int, total: int) -> None:
            nonlocal count, eta
            count = f"Classifying PRs: {done} of {total}"
            if done:
                remaining = (clock() - started) * (total - done) / done
                eta = str(timedelta(seconds=ceil(remaining)))
            if console.is_terminal:
                live.refresh()
            else:
                typer.echo(line(), err=True)

        yield update


def classify(
    model: str = typer.Option(DEFAULT_MODEL, help="Installed local Ollama model tag."),
    limit: int | None = typer.Option(None, min=1, help="Maximum pending merged PRs to process."),
    db: Path | None = DB_OPTION,
) -> None:
    """Classify previously unclassified merged PRs in the local cache."""
    try:
        with _timed_progress() as progress:
            counts = classify_pending(open_connection(db), model, limit, progress)
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        typer.echo(f"Classification failed: {exc}. Completed batches are saved.", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Classified {counts.total()} merged PRs.")
    for label, count in sorted(counts.items()):
        typer.echo(f"  {label}: {count}")

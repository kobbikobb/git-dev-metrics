from pathlib import Path

import requests
import typer

from ...cache import open_connection
from ...classification import DEFAULT_MODEL, classify_pending
from .._options import DB_OPTION


def classify(
    model: str = typer.Option(DEFAULT_MODEL, help="Installed local Ollama model tag."),
    limit: int | None = typer.Option(None, min=1, help="Maximum pending merged PRs to process."),
    db: Path | None = DB_OPTION,
) -> None:
    """Classify previously unclassified merged PRs in the local cache."""
    try:
        counts = classify_pending(open_connection(db), model, limit)
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        typer.echo(f"Classification failed: {exc}. Completed batches are saved.", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Classified {counts.total()} merged PRs.")
    for label, count in sorted(counts.items()):
        typer.echo(f"  {label}: {count}")

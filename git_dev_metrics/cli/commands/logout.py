import logging

import typer

from git_dev_metrics.github.auth_cache import delete_token

logger = logging.getLogger(__name__)


def logout() -> None:
    """Clear the stored GitHub token."""
    delete_token()
    typer.secho("Logged out successfully. Token cleared.", fg=typer.colors.GREEN)

from getpass import getpass

import typer

from .auth_cache import load_token, save_token, token_error
from .exceptions import GitHubAuthError


def _prompt_for_token() -> str:
    """Prompt user to input their GitHub fine-grained PAT."""
    typer.echo("Enter your GitHub fine-grained Personal Access Token (PAT).")
    typer.echo("Create one at: https://github.com/settings/tokens?type=beta")
    typer.echo("- Repository access: All repositories (or select specific repos)")
    typer.echo("- Permissions:")
    typer.echo("  - Contents: Read")
    typer.echo("  - Metadata: Read")
    typer.echo("  - Pull requests: Read")
    typer.echo("  - Actions: Read (build status in the stale report)")
    typer.echo("  - Dependabot alerts: Read (security badges in the stale report)")
    token = getpass("PAT: ")
    if not token:
        raise GitHubAuthError("No token provided")
    return token


def get_github_token() -> str:
    """Get GitHub token from keyring or prompt user for PAT."""
    cached_token = load_token()
    if cached_token and token_error(cached_token) is None:
        return cached_token

    token = _prompt_for_token()

    error = token_error(token)
    if error:
        raise GitHubAuthError(error)

    save_token(token)
    return token

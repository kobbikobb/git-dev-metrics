from getpass import getpass

from .auth_cache import is_token_valid, load_token, save_token
from .exceptions import GitHubAuthError


def _prompt_for_token() -> str:
    """Prompt user to input their GitHub PAT."""
    print("Enter your GitHub Personal Access Token (PAT).")
    print("Create one at: https://github.com/settings/tokens")
    print("Required scopes: repo, read:org")
    token = getpass("PAT: ")
    if not token:
        raise GitHubAuthError("No token provided")
    return token


def get_github_token() -> str:
    """Get GitHub token from keyring or prompt user for PAT."""
    cached_token = load_token()
    if cached_token and is_token_valid(cached_token):
        return cached_token

    token = _prompt_for_token()

    if not is_token_valid(token):
        raise GitHubAuthError("Invalid token. Please check your PAT and try again.")

    save_token(token)
    return token

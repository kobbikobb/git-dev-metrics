KNOWN_BOT_LOGINS: set[str] = {
    "dependabot",
    "dependabot[bot]",
    "snyk-io",
    "snyk[bot]",
    "renovate[bot]",
    "github-actions",
    "pipx[bot]",
    "poetry[bot]",
}


def is_bot(login: str) -> bool:
    """Check if a user is a known bot."""
    return login in KNOWN_BOT_LOGINS

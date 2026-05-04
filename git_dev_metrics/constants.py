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


def is_bot_login(login: str | None) -> bool:
    """True for known bots and any login ending in -bot or [bot]."""
    if not login:
        return False
    if login in KNOWN_BOT_LOGINS:
        return True
    return login.endswith("-bot") or login.endswith("[bot]")

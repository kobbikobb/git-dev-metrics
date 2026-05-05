KNOWN_BOT_LOGINS: set[str] = {
    "dependabot",
    "dependabot[bot]",
    "snyk-io",
    "snyk[bot]",
    "renovate[bot]",
    "github-actions",
    "pipx[bot]",
    "poetry[bot]",
    "copilot-pull-request-reviewer",
    "copilot-pull-request-reviewer[bot]",
    "copilot",
    "copilot[bot]",
}


def is_bot_login(login: str | None) -> bool:
    """True for known bots and any login ending in -bot, [bot], or matching common bot patterns."""
    if not login:
        return False
    if login in KNOWN_BOT_LOGINS:
        return True
    if login.endswith("-bot") or login.endswith("[bot]"):
        return True
    return login.startswith("copilot-") and login.endswith("-reviewer")

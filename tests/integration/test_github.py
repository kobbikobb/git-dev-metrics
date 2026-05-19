from datetime import UTC, datetime

from git_dev_metrics.github import fetch_repositories
from git_dev_metrics.github.queries import fetch_pull_requests
from git_dev_metrics.utils import TimePeriod


def test_fetch_repositories(
    github_token: str,
    my_vcr,
) -> None:
    with my_vcr.use_cassette("fetch_repositories.yaml"):
        repos = fetch_repositories(github_token)

    assert isinstance(repos, list)

    if repos:
        assert "full_name" in repos[0]
        assert "private" in repos[0]


def test_fetch_pull_requests(
    github_token: str,
    my_vcr,
) -> None:
    period = TimePeriod(
        since=datetime(2024, 1, 1, tzinfo=UTC), until=datetime(2024, 2, 1, tzinfo=UTC)
    )

    with my_vcr.use_cassette("fetch_pull_requests.yaml"):
        prs = fetch_pull_requests(
            github_token,
            org="your-org",
            repo="your-repo",
            period=period,
        )

    assert isinstance(prs, list)

    if prs:
        pr = prs[0]
        assert "number" in pr
        assert "title" in pr
        assert "merged_at" in pr

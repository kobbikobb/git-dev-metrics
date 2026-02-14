# Repo Improvements

## 5. Add Pagination

**File:** `git_dev_metrics/queries.py` line 51

You only fetch the first 100 PRs. Active repos like facebook/react will have way more than 100 merged PRs in 90 days.

**Fix:** Follow GitHub's `Link` header for pagination:

```python
def fetch_pull_requests(token: str, org: str, repo: str, since: datetime) -> list[PullRequest]:
    url = GITHUB_PULLS_URL.format(org=org, repo=repo)
    params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100}
    all_prs = []

    while url:
        response = requests.get(url, headers=get_api_headers(token), params=params, timeout=30)
        if response.status_code == 404:
            raise GitHubNotFoundError(f"Repository {org}/{repo} not found")
        response.raise_for_status()

        prs = response.json()
        if not prs:
            break

        for pr in prs:
            if pr.get("merged_at"):
                merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                if merged_date >= since:
                    all_prs.append(pr)
                else:
                    return all_prs  # PRs are sorted by updated desc, stop early

        # Follow pagination Link header
        url = response.links.get("next", {}).get("url")
        params = {}  # params are in the URL now

    return all_prs
```

The `response.links` dict is built-in to the `requests` library — it parses the `Link` header automatically.

---

## 6. Add Rate Limit Handling

**File:** `git_dev_metrics/queries.py`

GitHub allows 5000 requests/hour for authenticated users. You already have `GitHubRateLimitError` defined but never use it.

**Fix:** Check rate limit headers after each request. Create a helper:

```python
def _check_rate_limit(response: requests.Response) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None and int(remaining) == 0:
        reset_time = response.headers.get("X-RateLimit-Reset", "")
        raise GitHubRateLimitError(
            f"GitHub API rate limit exceeded. Resets at {reset_time}"
        )
```

Call this after every successful response, before processing the JSON.

---

## 7. Add Missing Tests

**Current coverage: 32%.** Here's what to add, roughly in priority order:

### a) Test queries.py with `responses` library

The `responses` library (already installed) lets you mock HTTP calls. Create `tests/test_queries.py`:

```python
import responses
from git_dev_metrics.queries import fetch_repositories, fetch_pull_requests

class TestFetchRepositories:
    @responses.activate
    def test_should_return_repositories_on_success(self):
        responses.add(
            responses.GET,
            "https://api.github.com/user/repos",
            json=[{"name": "my-repo", "full_name": "user/my-repo"}],
            status=200,
        )

        result = fetch_repositories("fake-token")

        assert len(result) == 1
        assert result[0]["name"] == "my-repo"

    @responses.activate
    def test_should_raise_on_unauthorized(self):
        responses.add(responses.GET, "https://api.github.com/user/repos", status=401)

        with pytest.raises(GitHubAPIError, match="Unauthorized"):
            fetch_repositories("bad-token")
```

### b) Test CLI with Typer's test runner

```python
from typer.testing import CliRunner
from git_dev_metrics.cli import app

runner = CliRunner()

class TestCLI:
    def test_should_show_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_should_reject_invalid_period(self):
        result = runner.invoke(app, ["analyze", "--org", "x", "--repo", "y", "--period", "abc"])
        assert result.exit_code != 0
```

### c) Move `any_pr` factory to `conftest.py`

Create `tests/conftest.py` and move the `any_pr()` helper there so all test files can reuse it:

```python
# tests/conftest.py
import pytest
from git_dev_metrics.types import PullRequest

def any_pr(**overrides) -> PullRequest:
    defaults = { ... }  # copy from test_reports.py
    return {**defaults, **overrides}

@pytest.fixture
def pr_factory():
    return any_pr
```

---

## 8. Add CLI Entry Point

**File:** `pyproject.toml`

Right now users must run `uv run python -m git_dev_metrics.cli`. Add a proper entry point:

```toml
[project.scripts]
git-dev-metrics = "git_dev_metrics.cli:app"
```

After `uv sync`, users can just run: `git-dev-metrics analyze ...`

---

## 9. Complete Project Metadata

**File:** `pyproject.toml`

Replace the placeholder description and add standard metadata:

```toml
[project]
name = "git-dev-metrics"
version = "0.1.0"
description = "CLI tool for analyzing GitHub development metrics"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Jakob Jonasson"}]

[project.urls]
Repository = "https://github.com/kobbikobb/git-dev-metrics"
```

---

## 10. Add Ruff Configuration

**File:** `pyproject.toml`

You're using ruff with zero configuration. Add rules to catch real bugs:

```toml
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort (import sorting)
    "B",    # flake8-bugbear (common bugs)
    "UP",   # pyupgrade (modernize syntax)
    "SIM",  # flake8-simplify
]
```

---

## 11. Add Pytest & Coverage Config

**File:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --strict-markers"

[tool.coverage.run]
source = ["git_dev_metrics"]

[tool.coverage.report]
fail_under = 60
```

The `fail_under` will make CI fail if coverage drops below 60%. Raise it as you add tests.

---

## 12. Consolidate Pyright Config

Delete `pyrightconfig.json` — it duplicates what's already in `pyproject.toml`. Update the pyproject.toml section:

```toml
[tool.pyright]
typeCheckingMode = "standard"
pythonVersion = "3.14"
```

---

## 13. Add Security Scanning to CI

**File:** `.github/workflows/ci.yml`

Add a security job:

```yaml
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv python install 3.14
    - run: uv sync
    - run: uv run pip-audit
```

Add `pip-audit` to your dev dependencies: `"pip-audit>=2.7.0"` in `[dependency-groups] dev`.

---

## 14. Add Dependabot

**Create file:** `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

This auto-creates PRs when dependencies have updates (like the manual cryptography bump you did).

---

## 15. Clean Up Miscellaneous

- **Delete** `format.sh` from root (keep `scripts/format.sh` only)
- **Delete** `pyrightconfig.json`
- **Update** `scripts/format.sh` to also format tests: `uv run ruff format git_dev_metrics tests`
- **Fix** inconsistent type hints in `reports.py`: use `list[X]` and `dict[X, Y]` everywhere (not `List`/`Dict` from typing)
- **Narrow** exception handling in `cli.py`: catch `GitHubError` instead of bare `Exception`, remove `traceback.print_exc()`
- **Add** `logging` — replace `print()` calls with `logger.info()`/`logger.debug()` so users can get verbose output with `--verbose`

---

## Suggested Order of Work

1. Fix test assertions (5 min, prevents silent bugs)
2. Clean pyproject.toml deps (10 min, removes bloat)
3. Fix CI Python version (2 min)
4. Add HTTP timeouts (5 min)
5. Add ruff/pytest/coverage config (10 min)
6. Add CLI entry point + metadata (5 min)
7. Consolidate pyright config (5 min)
8. Write query tests with `responses` (30-60 min)
9. Add pagination + rate limiting (30 min)
10. Add Dependabot + security scanning (10 min)
11. Everything else as time allows

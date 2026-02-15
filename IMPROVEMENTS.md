# Repo Improvements

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

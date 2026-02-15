# AGENTS.md - Developer Guidelines for git-dev-metrics

## Project Overview
git-dev-metrics is a CLI tool for analyzing GitHub development metrics. Uses Python 3.14, Typer for CLI, and Rich for terminal output.

---

## Build, Lint, and Test Commands

### Dependencies
```bash
uv sync              # Install dependencies
uv sync --all-extras # Install with dev dependencies
```

### Formatting and Linting
```bash
./scripts/format.sh                          # Full format (ruff check --fix + format)
uv run ruff check git_dev_metrics --fix      # Fix linting
uv run ruff format git_dev_metrics tests      # Format code
```

### Type Checking
```bash
uv run pyright
```

### Testing
```bash
uv run pytest tests/ -v                                    # All tests
uv run pytest tests/ --cov=git_dev_metrics --cov-report=term-missing  # With coverage
uv run pytest tests/test_reports.py -v                      # Specific file
uv run pytest tests/test_reports.py::TestCalculateCycleTime -v  # Specific class
uv run pytest tests/test_reports.py::TestCalculateCycleTime::test_should_return_zero_when_no_prs_provided -v  # Single test
./scripts/test.sh
```

### Running the Application
```bash
uv run app --help
uv run app analyze --org <org> --repo <repo> --period 30d
```

---

## Code Style Guidelines

### General
- **Line length**: 100 characters (pyproject.toml)
- **Python**: 3.14+
- **Type checking**: standard (strict)

### Imports
Use **relative imports** for internal modules, **absolute** for external:
```python
# Good
from datetime import datetime
import requests
from git_dev_metrics.queries import fetch_pull_requests
from .reports import get_pull_request_metrics
```
Order: stdlib, third-party, local

### Formatting
Use **ruff format** (4-space indent). Run `./scripts/format.sh` before committing.

### Type Annotations
- Use **PEP 604**: `str | None` not `Optional[str]`
- Use **TypedDict** for dict types
- All arguments/returns must have type hints
```python
def calculate_cycle_time(prs: list[PullRequest]) -> float:
    ...

class PullRequest(TypedDict):
    id: int
    title: str
```

### Naming
- **Functions/variables**: snake_case
- **Classes**: PascalCase
- **Constants**: SCREAMING_SNAKE_CASE
- **Private functions**: prefix `_`
- **Tests**: `Test<ClassName>`, method `test_should_<behavior>`

### Error Handling
Use custom exceptions (`git_dev_metrics/type_definitions.py`):
- `GitHubError` (base) → `GitHubAuthError`, `GitHubAPIError`, `GitHubRateLimitError`, `GitHubNotFoundError`

Use `from None` to suppress traceback, `typer.BadParameter` for CLI validation:
```python
raise GitHubNotFoundError(f"Repository {org}/{repo} not found")
raise typer.BadParameter("Period must be like '7d', '30d', '90d'") from None
```

### Docstrings
Google-style with Args, Returns, Raises. Keep concise.

### Tests
- Use pytest with class-based organization
- Use `conftest.py`'s `any_pr(**overrides)` fixture
- Use `responses` for HTTP mocking, `pytest.raises` for exceptions

---

## CI Pipeline (.github/workflows/ci.yml)
1. **test**: pytest + coverage → codecov
2. **lint**: ruff check, ruff format --check, pyright
3. **security**: pip-audit

---

## File Structure
```
git_dev_metrics/
  __init__.py, cli.py, client.py, date_utils.py, printer.py
  queries.py, reports.py, type_definitions.py
  auth/: github_auth.py, github_auth_cache.py
tests/: conftest.py, test_*.py
scripts/: test.sh, format.sh, run.sh
```

## Key Dependencies
typer, rich, pygithub, requests, python-dateutil, keyring, ruff, pyright, pytest, responses

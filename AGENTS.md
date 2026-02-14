# AGENTS.md - Development Guidelines

This file provides guidelines for agents working on the git-dev-metrics codebase.

## Project Overview

Git Dev Metrics is a Python tool for analyzing GitHub repository development metrics (cycle time, PR size, throughput). It uses FastAPI, typer for CLI, and pytest for testing.

## Build, Lint, and Test Commands

### Installation
```bash
uv sync              # Install all dependencies
uv sync --all-extras # Install with test dependencies
```

### Running Tests
```bash
# Run all tests with verbose output
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ --cov=git_dev_metrics --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_reports.py -v

# Run a specific test (most common way)
uv run pytest tests/test_reports.py::TestCalculateCycleTime::test_should_return_zero_when_no_prs_provided -v

# Run tests matching a pattern
uv run pytest -k "test_return_zero"
```

### Linting and Formatting
```bash
# Format code
uv run ruff format

# Check for linting issues
uv run ruff check git_dev_metrics

# Auto-fix linting issues
uv run ruff check --fix git_dev_metrics
```

### Type Checking
```bash
uv run pyright
```

### Running the CLI
```bash
uv run python -m git_dev_metrics.cli analyze --org <org> --repo <repo> --period 30d
```

## Code Style Guidelines

### General Principles
- **No comments** unless explicitly required by the task
- Use clear, descriptive names for functions and variables
- Keep functions small and focused on a single responsibility
- Use early returns to avoid deeply nested code

### Imports
- Use absolute imports for project modules: `from git_dev_metrics.types import ...`
- Use relative imports within the same package: `from .module import ...`
- Group imports in this order: standard library, third-party, local
- Use separate import groups with blank lines between

### Type Annotations
- Use Python 3.14+ type syntax with `typing` module support
- Use `TypedDict` for dictionary-based types (see `types.py`)
- Prefer explicit type annotations for function parameters and return types
- Use `list[T]`, `dict[K, V]` syntax (Python 3.9+)

Example:
```python
def calculate_cycle_time(prs: List[PullRequest]) -> float:
```

### Naming Conventions
- **Functions/variables**: snake_case (e.g., `calculate_cycle_time`, `prs`)
- **Classes**: PascalCase (e.g., `GitHubClient`, `TestCalculateCycleTime`)
- **Constants**: SCREAMING_SNAKE_CASE (e.g., `DEFAULT_PERIOD`)
- **Private functions**: prefix with underscore (e.g., `_internal_function`)
- **File names**: snake_case (e.g., `github_auth.py`)

### Exception Handling
- Create custom exceptions inheriting from a base exception class
- Base exception: `GitHubError(Exception)`
- Specific exceptions inherit from `GitHubError` (e.g., `GitHubAuthError`, `GitHubAPIError`)
- Use descriptive exception messages
- Handle exceptions at the appropriate level (propagate or catch specifically)

Example:
```python
class GitHubError(Exception):
    """Base exception for GitHub API errors."""
    pass

class GitHubAuthError(GitHubError):
    """Authentication failed."""
    pass
```

### Error Handling in CLI
- Use try/except blocks with specific exception types
- Use `typer.secho()` for colored output (errors in red, success in green)
- Call `traceback.print_exc()` for debugging
- Exit with appropriate code: `raise typer.Exit(code=1)`

### Test Structure
- Use pytest with test classes for grouping related tests
- Test class naming: `Test<ClassName>` or `Test<FunctionName>`
- Test method naming: `test_<expected_behavior>`
- Use helper functions like `any_pr()` to create test fixtures with defaults

Example:
```python
def any_pr(**overrides: Any) -> PullRequest:
    """Create a PullRequest with sensible defaults for testing."""
    defaults: PullRequest = {
        "id": 1,
        "number": 1,
        ...
    }
    return {**defaults, **overrides}

class TestCalculateCycleTime:
    def test_return_zero_when_no_prs_provided(self):
        prs = []
        result = calculate_cycle_time(prs)
        assert result == 0.0
```

### Project Structure
```
git_dev_metrics/
├── __init__.py       # Package exports
├── __main__.py       # Entry point
├── cli.py            # Typer CLI commands
├── client.py         # GitHub API client
├── reports.py        # Metrics calculation functions
├── types.py          # TypedDict definitions and exceptions
├── queries.py        # API query functions
├── printer.py        # Output formatting
├── date_utils.py     # Date/time utilities
└── auth/
    ├── github_auth.py
    └── github_auth_cache.py

tests/
├── test_reports.py
├── test_date_utils.py
└── test_exceptions.py
```

### Configuration
- Python 3.14+ required
- Uses `uv` for package management
- Uses `ruff` for linting and formatting
- Uses `pyright` for type checking (configured in `pyrightconfig.json`)
- Uses `pytest` with `pytest-mock`, `pytest-cov`, `responses` for testing

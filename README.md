# Git Dev Metrics

## Getting started
- uv sync

## Queries
- uv run python -m git_dev_metrics.cli kobbikobb git-dev-metrics

## Testing
- Run all tests: `uv run pytest tests/ -v`
- Run tests with coverage: `uv run pytest tests/ --cov=git_dev_metrics --cov-report=term-missing`
- Run specific test file: `uv run pytest tests/test_reports.py -v`
- Run specific test: `uv run pytest tests/test_reports.py::TestCalculateCycleTime::test_should_return_zero_when_no_prs_provided -v`

### Test Structure
- `tests/test_reports.py` - Tests for metrics calculation functions
- `tests/test_exceptions.py` - Tests for custom exception classes
- `tests/conftest.py` - Shared test fixtures and configuration

# Git Dev Metrics

## Getting started
- uv sync
- uv run app --help

## Linting and Formatting  
- uv run ruff format
- uv run ruff check

## Integration Tests (GitHub API)

Integration tests use VCR to record GitHub API interactions.

Recorded HTTP responses are stored in:
tests/integration/cassettes/

### Running tests

uv run pytest

### Re-recording cassettes

To refresh recordings:

GITHUB_TOKEN=your_token uv run pytest tests/integration

Cassettes are committed to the repository to ensure deterministic CI runs.

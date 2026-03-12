# Git Dev Metrics

## Getting started
- uv sync
- uv run app --help

## Usage

```bash
# Analyze a repository (prompts for token if needed)
uv run app --org myorg --repo myrepo

# With custom period
uv run app --org myorg --repo myrepo --period 7d

# With custom output path
uv run app --org myorg --repo myrepo --output ./my-metrics.md
```

### Options
- `--org` - GitHub organization name
- `--repo` - Repository name  
- `--period` - Time period (e.g., 7d, 30d, 90d) [default: 30d]
- `--output` - Output file path (default: ./metrics_results/metrics_TIMESTAMP.md)

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

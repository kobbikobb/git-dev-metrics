# Git Dev Metrics

CLI tool for analyzing GitHub development metrics across teams and repos.

## Setup

```bash
uv sync
uv run app --help
```

## Usage

```bash
# Pull PR data for a repo/month into the local cache
uv run app pull --org myorg --repo myrepo

# Render the HTML dashboard (flag mode)
uv run app dashboard --from 2026-04 --to 2026-04

# Render the HTML dashboard (wizard mode — pick from cached months)
uv run app dashboard

# Print dashboard summary to console
uv run app summary --from 2026-04 --to 2026-04

# Multi-month trend report
uv run app trend --from 2026-01 --to 2026-04

# Find stale PRs across repos
uv run app stale

# Clear local cache
uv run app clear

# Manage GitHub token
uv run app logout
```

## Available Commands

| Command | Description |
|---------|-------------|
| `pull` | Pull a sealed month of PRs for one repository into the cache |
| `dashboard` | Render the in-depth HTML dashboard and open it in the browser |
| `summary` | Print the dashboard summary to the console |
| `trend` | Render a multi-month trend HTML aggregated across all cached repos |
| `stale` | Find stale PRs across synced repos |
| `clear` | Delete the entire local cache database |
| `logout` | Clear the stored GitHub token |

## Linting & Formatting

```bash
./scripts/format.sh
uv run pytest
```

## Project Structure

```
git_dev_metrics/
  cli/           — Typer CLI commands and wizards
  cache/         — SQLite cache for PRs and reviews
  github/        — GitHub GraphQL API client
  metrics/       — Metric calculations and report printers
  models/        — TypedDict definitions
  utils/         — Date/time helpers
tests/
  unit/          — Unit tests (mocked GitHub API)
  integration/   — Integration tests (VCR-recorded API calls)
```

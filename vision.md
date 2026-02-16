# git-dev-metrics Vision

## Mission
A simple, CLI-only tool that helps teams understand developer impact and identify bottlenecks by analyzing GitHub data—without expensive enterprise platforms.

## Core Principles
- **CLI-first**: No web UI, no server. Run locally, export as needed.
- **GraphQL-powered**: Efficient, single-request data fetching from GitHub.
- **Multi-repo tracking**: Configure a list of repos to analyze together.
- **GitHub-only**: No other integrations. Works with free GitHub plans.
- **Minimal state**: Optional SQLite for historical tracking (phase 2).

## What We Track

### 1. Developer Impact
- PR count, throughput, cycle time per developer
- Review contributions (reviews given/received)
- Code review turnaround time
- **Team-level aggregation**: Group metrics by GitHub teams

### 2. Bottleneck Detection
- PR aging (how long PRs sit waiting)
- Review latency (first review comment time)
- Identify overwhelmed reviewers or stalled PRs
- **Team-level bottlenecks**: Which teams are blocking others

### 3. AI Adoption & Impact (simple, free)
- **Co-Authored-By detection**: Parse commit metadata for AI co-authors
- **AI-labeled PRs**: Track PRs labeled as AI-assisted
- **Team AI adoption**: Which teams use AI most (normalized by team size)
- **AI velocity impact**: Compare cycle time & PR size: AI-assisted vs non-AI

## What's Out of Scope
- DORA metrics (requires CI/CD pipeline data)
- SPACE metrics (requires survey/tooling data)
- Enterprise-only GitHub features (Copilot API)
- Cost tracking

## Data Sources
- GitHub GraphQL API (primary)
- Co-Authored-By commit metadata
- GitHub Teams (free, available on all plans)
- PR labels

## Output
- CLI table output (Rich)
- JSON/CSV export for external dashboards
- Team and individual developer views

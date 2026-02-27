# AI-Powered Git Workflows with OpenCode

A recipe for adding autonomous AI agents to any GitHub repository — handling PR reviews, issue triage, issue implementation, review fixes, and security remediation. Uses [OpenCode](https://opencode.ai/) with free/cheap models.

This is adapted from a production setup using Claude Code + Anthropic API. The OpenCode equivalents use the `anomalyco/opencode/github@v1` action with Gemini, Copilot, or any provider you configure.

---

## The Full Loop

```
Issue opened
  → AI triages, labels, comments         (issue-triage.yml)
  → Human adds "approved" label
  → AI implements on branch, opens PR     (issue-implement.yml)
  → AI reviews the PR                     (pr-review.yml)
  → If changes requested on bot PRs:
      → AI fixes review feedback          (pr-review-fix.yml)
  → CI passes → merge

Security alert found by CodeQL
  → AI fixes it, opens PR                (codeql-fix.yml)
```

---

## Prerequisites

1. **OpenCode Agent GitHub App** — Install from the [GitHub Marketplace](https://github.com/apps/opencode-agent). This is **required** for the action to work — it provides the bot identity and permissions. Alternatively, set `use_github_token: true` in the action config and use `GITHUB_TOKEN` (loses bot identity — comments appear as "github-actions[bot]").
2. **`anomalyco/opencode/github@v1`** — The GitHub Action (pinned to v1 for stability).
3. **Model provider API key** — Set as repo secret (e.g. `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, or use GitHub Copilot).
4. **`AGENTS.md`** in your repo root — OpenCode's equivalent of `CLAUDE.md`. Run `opencode /init` locally to generate one.

### Free/Cheap Model Options

| Provider | Model | Cost | Setup |
|----------|-------|------|-------|
| GitHub Copilot | Via subscription | Free with Copilot Pro | `opencode /connect` → GitHub |
| Google Gemini | `google/gemini-2.5-flash` | Free tier (see limits below) | `GEMINI_API_KEY` secret |
| Google Gemini | `google/gemini-2.5-pro` | Paid tier recommended | `GEMINI_API_KEY` secret |
| OpenRouter | Many models | Pay-per-token | `OPENROUTER_API_KEY` secret |

> **Gemini free tier reality check:** The free tier is limited to ~5 requests per minute and ~25 requests per day. This is fine for low-traffic repos (a few PRs/issues per day) but will hit rate limits on active repos. **Use `gemini-2.5-flash` for free tier** — it's faster and uses less quota. For active repos or production use, use a paid API key or switch to Copilot.

In the workflow examples below, replace the model value with your chosen `provider/model`.

---

## Getting Started

**Start with PR Review only.** It's the highest-value, lowest-risk workflow — it doesn't write code or push branches, just leaves review comments. Once you're comfortable with how the AI behaves on your codebase, add workflows incrementally:

1. **PR Review** — read-only, low risk
2. **Issue Triage** — read-only, low risk
3. **Issue Implementation** — writes code, medium risk
4. **PR Review Fix** — writes code, medium risk (only on bot PRs)
5. **CodeQL Fix** — writes code, medium risk (only for security alerts)

---

## 1. Project Instructions — `AGENTS.md`

Create this file in your repo root. It tells the AI about your project:

```markdown
# AGENTS.md

## Overview
Brief description of what this project does.

## Development Commands
- `npm test` — run tests
- `npm run lint` — run linter
- `npm run format` — format code

## Code Style
- Describe conventions (naming, patterns, etc.)
- Test descriptions must start with "should"

## Architecture
- Key directories and what they contain
- Important patterns to follow
```

---

## 2. PR Review — `pr-review.yml`

Automatically reviews every non-draft PR when opened or updated.

```yaml
name: PR Review

on:
  pull_request:
    types: [opened, ready_for_review, synchronize]

concurrency:
  group: pr-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    continue-on-error: true
    permissions:
      contents: read
      pull-requests: write
      issues: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - name: Check if re-review needed
        id: check
        if: github.event.action == 'synchronize'
        run: |
          REVIEWS=$(gh api repos/${{ github.repository }}/pulls/${{ github.event.pull_request.number }}/reviews)
          # Note: if using use_github_token, the bot login is "github-actions[bot]" instead
          PENDING=$(echo "$REVIEWS" | jq '[.[] | select(.user.login == "opencode-agent[bot]" and .state == "CHANGES_REQUESTED")] | length')
          echo "should_review=$([[ $PENDING -gt 0 ]] && echo true || echo false)" >> $GITHUB_OUTPUT
        env:
          GH_TOKEN: ${{ github.token }}

      - uses: anomalyco/opencode/github@v1
        if: github.event.action != 'synchronize' || steps.check.outputs.should_review == 'true'
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        with:
          model: google/gemini-2.5-pro
          prompt: |
            Review PR #${{ github.event.pull_request.number }}.

            Look at all changed files. For each issue found, post a review comment
            on the specific file and line. Consider:
            - Bugs, logic errors, edge cases
            - Security issues (injection, auth, data exposure)
            - Style violations per AGENTS.md
            - Missing tests for new behavior

            If everything looks good, approve. Otherwise request changes.
```

---

## 3. Issue Triage — `issue-triage.yml`

Auto-triage new issues: add labels, comment with analysis, flag duplicates.

```yaml
name: Issue Triage

on:
  issues:
    types: [opened]

concurrency:
  group: issue-triage-${{ github.event.issue.number }}
  cancel-in-progress: true

jobs:
  triage:
    runs-on: ubuntu-latest
    continue-on-error: true
    permissions:
      contents: read
      issues: write
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: anomalyco/opencode/github@v1
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        with:
          model: google/gemini-2.5-pro
          prompt: |
            Triage issue #${{ github.event.issue.number }}.

            1. Read the issue
            2. Search the codebase to understand if it's valid
            3. Check for duplicate issues with `gh search issues`
            4. Add appropriate labels (bug, enhancement, documentation, etc.)
            5. Comment with:
               - Whether you could reproduce / confirm the issue from code reading
               - Which files are likely involved
               - Suggested priority (critical / high / medium / low)
               - Any duplicate issues found
            6. Add the "triaged" label when done
```

---

## 4. Issue Implementation — `issue-implement.yml`

When a triaged issue gets the `approved` label, AI implements it on a branch and opens a PR. OpenCode handles git operations (branching, committing, pushing, PR creation) automatically — do not add manual git steps.

```yaml
name: Issue Implementation

on:
  issues:
    types: [labeled]

concurrency:
  group: issue-implement-${{ github.event.issue.number }}
  cancel-in-progress: true

jobs:
  implement:
    if: |
      github.event.label.name == 'approved' &&
      contains(github.event.issue.labels.*.name, 'triaged')
    runs-on: ubuntu-latest
    continue-on-error: true
    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: anomalyco/opencode/github@v1
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        with:
          model: google/gemini-2.5-pro
          prompt: |
            Implement issue #${{ github.event.issue.number }}.

            1. Read the issue thoroughly
            2. Explore the codebase to understand the architecture
            3. Implement the fix or feature
            4. Run tests and linters (see AGENTS.md for commands)
            5. Fix any failures
            6. Create a PR linking to the issue

            Keep changes minimal and focused. Follow existing patterns.
```

---

## 5. PR Review Fix — `pr-review-fix.yml`

When a bot-created PR gets `changes_requested`, automatically fix the feedback. Includes a loop counter to prevent infinite fix cycles.

```yaml
name: PR Review Fix

on:
  pull_request_review:
    types: [submitted]

concurrency:
  group: pr-review-fix-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  fix:
    if: |
      github.event.review.state == 'changes_requested' &&
      contains(github.event.pull_request.labels.*.name, 'bot-automated')
    runs-on: ubuntu-latest
    continue-on-error: true
    permissions:
      contents: write
      pull-requests: write
      id-token: write
    steps:
      - name: Check fix attempt count
        id: counter
        run: |
          COMMENTS=$(gh api repos/${{ github.repository }}/issues/${{ github.event.pull_request.number }}/comments \
            --jq '[.[] | select(.body | startswith("🔧 Auto-fix attempt"))] | length')
          echo "attempts=$COMMENTS" >> $GITHUB_OUTPUT
          if [ "$COMMENTS" -ge 3 ]; then
            echo "limit_reached=true" >> $GITHUB_OUTPUT
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "⚠️ Auto-fix limit reached (3 attempts). Needs human review."
          else
            echo "limit_reached=false" >> $GITHUB_OUTPUT
          fi
        env:
          GH_TOKEN: ${{ github.token }}

      - uses: actions/checkout@v4
        if: steps.counter.outputs.limit_reached == 'false'
        with:
          ref: ${{ github.event.pull_request.head.ref }}
          fetch-depth: 0

      - uses: anomalyco/opencode/github@v1
        if: steps.counter.outputs.limit_reached == 'false'
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        with:
          model: google/gemini-2.5-pro
          prompt: |
            Fix the review feedback on PR #${{ github.event.pull_request.number }}.

            1. Read all review comments requesting changes
            2. Address each comment
            3. Run tests and linters
            4. Commit and push the fixes

            After pushing, comment "🔧 Auto-fix attempt ${{ steps.counter.outputs.attempts }}" on the PR.
```

---

## 6. CodeQL Security Fix — `codeql-fix.yml`

After CodeQL finds vulnerabilities, auto-fix them. OpenCode handles git operations automatically.

```yaml
name: CodeQL Fix

on:
  workflow_run:
    workflows: ["CodeQL"]
    types: [completed]
    branches: [main]

concurrency:
  group: codeql-fix
  cancel-in-progress: false

jobs:
  get-alerts:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    permissions:
      security-events: read
    outputs:
      matrix: ${{ steps.alerts.outputs.matrix }}
      has_alerts: ${{ steps.alerts.outputs.has_alerts }}
    steps:
      - name: Fetch open alerts
        id: alerts
        run: |
          ALERTS=$(gh api "repos/${{ github.repository }}/code-scanning/alerts?state=open&per_page=5" \
            --jq '[.[] | {"alert_number": .number}]' 2>/dev/null) || {
            echo "::warning::Failed to fetch CodeQL alerts (check security-events permission)"
            echo "has_alerts=false" >> "$GITHUB_OUTPUT"
            echo "matrix={}" >> "$GITHUB_OUTPUT"
            exit 0
          }
          COUNT=$(echo "$ALERTS" | jq 'length')
          if [ "$COUNT" -eq 0 ]; then
            echo "has_alerts=false" >> "$GITHUB_OUTPUT"
            echo "matrix={}" >> "$GITHUB_OUTPUT"
          else
            echo "has_alerts=true" >> "$GITHUB_OUTPUT"
            echo "matrix={\"include\":$(echo $ALERTS)}" >> "$GITHUB_OUTPUT"
          fi
        env:
          GH_TOKEN: ${{ github.token }}

  fix:
    needs: get-alerts
    if: needs.get-alerts.outputs.has_alerts == 'true'
    runs-on: ubuntu-latest
    continue-on-error: true
    strategy:
      fail-fast: false
      max-parallel: 1
      matrix: ${{ fromJson(needs.get-alerts.outputs.matrix) }}
    permissions:
      contents: write
      pull-requests: write
      security-events: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - name: Get alert details
        id: alert
        run: |
          DETAILS=$(gh api "repos/${{ github.repository }}/code-scanning/alerts/${{ matrix.alert_number }}") || {
            echo "::warning::Failed to fetch alert details"
            exit 1
          }
          echo "json<<EOF" >> "$GITHUB_OUTPUT"
          echo "$DETAILS" >> "$GITHUB_OUTPUT"
          echo "EOF" >> "$GITHUB_OUTPUT"
        env:
          GH_TOKEN: ${{ github.token }}

      - uses: anomalyco/opencode/github@v1
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        with:
          model: google/gemini-2.5-pro
          prompt: |
            Fix CodeQL alert #${{ matrix.alert_number }}.

            Alert details:
            ```json
            ${{ steps.alert.outputs.json }}
            ```

            Read the affected file, understand the vulnerability, apply the minimal fix.
            Do not refactor surrounding code. Run linters after fixing.
            Open a PR with the fix.
```

---

## Design Patterns

### GitHub App vs `GITHUB_TOKEN`

The **OpenCode Agent GitHub App** is the recommended setup — install it from the Marketplace. It provides a dedicated bot identity (avatar, name) and avoids triggering workflow loops (actions by apps don't re-trigger `on: push`).

If you use `use_github_token: true` instead, add guards to prevent infinite loops:

```yaml
    if: github.actor != 'github-actions[bot]'
```

Note: with `use_github_token`, the bot username is `github-actions[bot]` rather than `opencode-agent[bot]` — update any username checks in your workflows accordingly.

### Labeling for control flow

Use labels as state machines:
- `triaged` — issue has been analyzed
- `approved` — human approved for implementation
- `bot-automated` — PR was created by the bot (enables auto-fix on review)

### Concurrency guards

Prevent duplicate runs:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.event.issue.number }}
  cancel-in-progress: true
```

### `continue-on-error: true`

AI workflows should never block your CI. Always add this to AI jobs so failures are informational.

### Structured output

Both Claude Code Action and OpenCode support JSON schema output for programmatic parsing of AI responses (verdict, comments, status, etc.).

---

## Adapting to Your Stack

1. Install the **OpenCode Agent** GitHub App on your repository
2. Copy the workflow files you want into `.github/workflows/`
3. Create `AGENTS.md` with your project's commands and conventions
4. Add your API key as a repository secret
5. Create labels: `triaged`, `approved`, `bot-automated`
6. Push and open a test PR to verify the setup

---

## Troubleshooting

### OpenCode Agent app not installed
**Symptom:** Action fails immediately with permission or authentication errors.
**Fix:** Install the [OpenCode Agent app](https://github.com/apps/opencode-agent) on your repo. Or set `use_github_token: true` in the action config.

### Token permission errors
**Symptom:** `Resource not accessible by integration` or 403 errors.
**Fix:** Ensure the `permissions:` block in your workflow includes all required scopes. For org repos, check that GitHub Actions has "Read and write" permission in Settings → Actions → General.

### Rate limits on free tier
**Symptom:** `429 Too Many Requests` or `RESOURCE_EXHAUSTED` errors from Gemini.
**Fix:** Switch to `gemini-2.5-flash` (lower quota cost), reduce concurrent workflows, or upgrade to a paid API key. The free tier supports ~5 RPM / ~25 RPD.

### Infinite review-fix loops
**Symptom:** The bot keeps pushing fixes and re-reviewing endlessly.
**Fix:** The `pr-review-fix.yml` above includes a 3-attempt counter. Ensure the `bot-automated` label is only on bot-created PRs, and that `concurrency` groups are set to cancel duplicate runs.

### Bot comments appear as "github-actions"
**Symptom:** Comments don't show the OpenCode bot avatar/name.
**Fix:** This happens when using `use_github_token: true` instead of the GitHub App. Install the OpenCode Agent app for proper bot identity.

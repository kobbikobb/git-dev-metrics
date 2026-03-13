# AGENTS.md

See [VISION.md](./VISION.md) for project goals, architecture decisions, and roadmap.

## Stack
Python 3.14+, Typer (CLI), Rich (terminal output), uv (package manager)

## Commands

| Task | Command |
|------|---------|
| Install deps | `uv sync --all-extras` |
| Format + lint | `./scripts/format.sh` |
| Type check | `uv run pyright` |
| Test | `./scripts/test.sh` |
| Test (coverage) | `uv run pytest tests/ --cov=git_dev_metrics --cov-report=term-missing` |
| Single test | `uv run pytest path/to/test.py::Class::method -v` |
| Run app | `uv run app analyze --org <org> --repo <repo> --period 30d` |

## Code Style

- Line length: 100 chars
- Imports: relative for internal, absolute for external; order: stdlib → third-party → local
- Types: PEP 604 (`str | None`), TypedDict for dicts, all args/returns annotated
- Naming: `snake_case` functions/vars, `PascalCase` classes, `SCREAMING_SNAKE_CASE` constants, `_prefix` private
- Docstrings: Google-style (Args, Returns, Raises), concise
- Errors: custom exceptions from `type_definitions.py` (`GitHubError` hierarchy); `from None` to suppress tracebacks

## Code Quality Rules

| Rule | Limit | Enforcement |
|------|-------|-------------|
| Max function length | 30 lines | Manual review |
| Max complexity | 10 | `ruff check .` (C901) |
| Max file length | 400 lines | Manual review |
| Line length | 100 chars | `ruff format` |
| Minimal nesting | - | Prefer flat code, extract helpers |

Run `ruff check .` to verify complexity.

## Consistency Guidelines

- **Types**: Always use defined TypedDicts from `models/` (e.g., `PullRequest`, `OpenPullRequest`). Never return raw `dict` unless truly generic.
- **Datetime fields**: Use ISO strings (`str`) in models/mappings, convert to `datetime` internally only when needed for calculations.
- **Testability**: When code depends on `datetime.now()` or similar, inject a `clock` parameter (e.g., `clock: Callable[[], datetime] | None = None`) so tests can provide deterministic values.
- **Follow existing patterns**: Check similar functions in the codebase before adding new patterns (e.g., how `fetch_repo_metrics` returns typed data).

## Testing

- pytest, class-based: `Test<ClassName>` / `test_should_<behavior>`
- Use `any_pr(**overrides)` fixture from `conftest.py`
- Mock HTTP with `responses` library
- For time-dependent logic, inject a `clock` parameter and pass `lambda: known_time` in tests

## CI
lint → test+coverage → security audit (pip-audit)

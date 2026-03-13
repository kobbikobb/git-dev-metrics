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

1. **Max function length: 30 lines** - Keep functions short and focused
2. **Max complexity: 10** (C901) - Limit branching + nesting depth
3. **Minimal nesting** - Prefer flat code, extract helper functions

Run `ruff check .` to verify.

## Testing

- pytest, class-based: `Test<ClassName>` / `test_should_<behavior>`
- Use `any_pr(**overrides)` fixture from `conftest.py`
- Mock HTTP with `responses` library

## CI
lint → test+coverage → security audit (pip-audit)

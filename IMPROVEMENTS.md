# Repo Improvements


## 12. Consolidate Pyright Config

Delete `pyrightconfig.json` — it duplicates what's already in `pyproject.toml`. Update the pyproject.toml section:

```toml
[tool.pyright]
typeCheckingMode = "standard"
pythonVersion = "3.14"
```

---

## 13. Add Security Scanning to CI

**File:** `.github/workflows/ci.yml`

Add a security job:

```yaml
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv python install 3.14
    - run: uv sync
    - run: uv run pip-audit
```

Add `pip-audit` to your dev dependencies: `"pip-audit>=2.7.0"` in `[dependency-groups] dev`.

---

## 14. Add Dependabot

**Create file:** `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

This auto-creates PRs when dependencies have updates (like the manual cryptography bump you did).

---

## 15. Clean Up Miscellaneous

- **Delete** `format.sh` from root (keep `scripts/format.sh` only)
- **Delete** `pyrightconfig.json`
- **Update** `scripts/format.sh` to also format tests: `uv run ruff format git_dev_metrics tests`
- **Fix** inconsistent type hints in `reports.py`: use `list[X]` and `dict[X, Y]` everywhere (not `List`/`Dict` from typing)
- **Narrow** exception handling in `cli.py`: catch `GitHubError` instead of bare `Exception`, remove `traceback.print_exc()`
- **Add** `logging` — replace `print()` calls with `logger.info()`/`logger.debug()` so users can get verbose output with `--verbose`

---

## Suggested Order of Work

1. Fix test assertions (5 min, prevents silent bugs)
2. Clean pyproject.toml deps (10 min, removes bloat)
3. Fix CI Python version (2 min)
4. Add HTTP timeouts (5 min)
5. Add ruff/pytest/coverage config (10 min)
6. Add CLI entry point + metadata (5 min)
7. Consolidate pyright config (5 min)
8. Write query tests with `responses` (30-60 min)
9. Add pagination + rate limiting (30 min)
10. Add Dependabot + security scanning (10 min)
11. Everything else as time allows

# Repository guidance

## Python environment

- Use Python 3.11. The `.python-version` file pins the local interpreter, and `pyproject.toml` constrains supported versions to `>=3.11,<3.12`.
- Use `uv` for environment and dependency management. Do not manage this project with a separate `pip` workflow.
- Set up or synchronize the environment with `uv sync --all-groups`.
- Run project commands through `uv run`, for example `uv run uvicorn app.main:app --reload` and `uv run pytest`.
- Add and remove runtime dependencies with `uv add <package>` and `uv remove <package>`. Use `uv add --dev <package>` and `uv remove --dev <package>` for development dependencies.
- Keep `uv.lock` committed and synchronized with `pyproject.toml`. Do not commit `.venv`, local SQLite database files, or Python cache files.
- Ruff is the sole Python linter and formatter. Its strict rule set and format policy live in `pyproject.toml`; do not add conflicting formatters or override its rules casually.
- Before handing off Python changes, run `uv run ruff check .` and `uv run ruff format --check .`. To apply fixes, run `uv run ruff check . --fix` followed by `uv run ruff format .`.
- The canonical quality gate is `./scripts/check.sh`. It runs Ruff lint, format check, and the complete pytest suite with locked dependencies. Run it after each meaningful implementation change and before handoff.
- Apply safe lint and format fixes with `./scripts/fix.sh`, then rerun `./scripts/check.sh`.
- Git pre-commit delegates to the same quality gate. Enable it for a checkout with `./scripts/install-git-hooks.sh`; do not bypass it for normal commits.

## Project conventions

- The backend uses FastAPI, SQLAlchemy, Alembic, and SQLite as described in `docs/TSD.md` and `docs/DATABASE.md`.
- Keep API behavior aligned with `docs/PRD.md`; update the relevant docs when an approved design decision changes.
- Bind the unauthenticated local development server to `127.0.0.1` by default.

## Agent development loop

1. Read this file and the relevant product, technical, database, and test-case docs before editing. Turn the requested outcome into observable acceptance criteria.
2. Implement one small vertical slice at a time. For behavior covered by `docs/TEST_CASE.md`, add or update the automated test with the implementation.
3. Run the narrow relevant test while iterating, then run `./scripts/check.sh` before handoff. If a check fails, use its output to fix the code and rerun the gate; do not weaken a rule or delete a failing assertion just to get a green result.
4. Inspect the final diff for unintended changes and update the docs when behavior or design changes.
5. Report what changed and the exact checks run. Never claim a check passed if it was not run.

The quality gate is deterministic and runs locally, before commits, and in GitHub Actions. Keep agent-specific behavioral evals out of the MVP until there is an agent workflow to measure; add a small eval for a concrete repeated failure when one appears.

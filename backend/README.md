# Inai backend

FastAPI backend for the Inai MVP. Requirements, design and tasks: `.kiro/specs/inai-mvp/`.

## Approved stack (M1)
Python 3.11, uv, FastAPI, Uvicorn, SQLAlchemy 2, Alembic, firebase-admin, pytest, PostgreSQL 16 (local-only for development). Authentication is tested with test doubles; the Firebase emulator is not used yet.

## Setup
```bash
cd backend
uv lock            # first time only; commit uv.lock
uv sync --locked   # creates .venv with exact locked versions
```

## Quality checks
```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

## Status
`uv.lock` has not been generated yet: the development sandbox has no package-index access. Until it exists, `uv sync --locked` and CI fail by design. See the M1 readiness report.

## Rules
- No production credentials, no real user data, no audio persistence.
- Identity comes only from verified Firebase tokens (test doubles in tests).
- The language catalog starts empty; no language is verified without evidence.

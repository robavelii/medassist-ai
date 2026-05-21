# Alembic migrations

This folder contains the database migration scripts for the project. Alembic is configured to use SQLite by default and to autogenerate migrations from the SQLAlchemy models in `src/models`.

## Overview

- Script location: `alembic/`
- Revisions: `alembic/versions/`
- Config: `alembic.ini` (default URL: `sqlite:///db.sqlite3`)
- Metadata source for autogenerate: `src.models.llm_cache_model.Base` (see `alembic/env.py`)

## Prerequisites

- Python and dependencies installed (the repo uses `uv` with `pyproject.toml`/`uv.lock`).
- Run all commands from the project root.

Tip: If using `uv`, prefix commands with `uv run`. Examples below use `uv`.

## Common commands

- Create a new revision from model changes (autogenerate):

  - `uv run alembic revision --autogenerate -m "describe changes"`

- Apply migrations (to latest):

  - `uv run alembic upgrade head`

- Downgrade one step:

  - `uv run alembic downgrade -1`

- Show current revision:

  - `uv run alembic current`

- Show history:

  - `uv run alembic history --verbose`

- Stamp the database without running migrations (use with care):
  - `uv run alembic stamp head`

## Autogenerate notes

- `alembic/env.py` sets `target_metadata` to `src.models.llm_cache_model.Base`. Ensure all declarative models are part of that Base (or update `env.py` to include additional metadata) so `--autogenerate` sees schema changes.
- Autogeneration detects structural changes; you should still review and edit the generated revision scripts before applying.

## Switching databases

- Edit `sqlalchemy.url` in `alembic.ini`.
  - SQLite (default): `sqlite:///db.sqlite3`
  - PostgreSQL (example): `postgresql+psycopg://user:pass@localhost:5432/dbname`
  - MySQL (example): `mysql+pymysql://user:pass@localhost:3306/dbname`
- Make sure the proper DB driver is installed in your environment.

## Reset local SQLite (dev only)

If you need a clean DB during development:

1. Stop anything using the DB.
2. Delete the file `db.sqlite3`.
3. Recreate schema:

- `uv run alembic upgrade head`

## Troubleshooting

- Import errors (e.g., cannot import `src...`): run commands from the project root; `alembic.ini` sets `prepend_sys_path = .` which should expose `src`.
- SQLite database is locked: close other processes using `db.sqlite3` and retry.
- Autogenerate misses changes: confirm your models are attached to the configured `Base` or update `target_metadata` in `alembic/env.py`.

## Existing revisions

- Example: `alembic/versions/e5b4f6f9ca59_create_llm_cache_model.py`

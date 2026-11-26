"""Alembic environment.

The database URL comes from the ``INAI_DATABASE_URL`` environment variable and is never
written to a file. Tests pass an already-open connection through
``config.attributes["connection"]`` so each test run can use its own schema.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, create_engine

from inai_backend.db import models as _models  # noqa: F401  (registers tables on Base.metadata)
from inai_backend.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    provided = config.attributes.get("connection")
    if provided is not None:
        _run(provided)
        return

    url = os.environ.get("INAI_DATABASE_URL")
    if not url:
        raise RuntimeError("Set INAI_DATABASE_URL to run migrations (no default is provided).")
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            _run(connection)
            connection.commit()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Offline (--sql) migrations are not supported for this project.")

run_migrations_online()

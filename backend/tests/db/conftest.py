"""PostgreSQL fixtures for schema tests (T1.2).

Each test gets a fresh, uniquely named schema, migrated to head, and dropped afterwards.

- ``INAI_TEST_DATABASE_URL`` (SQLAlchemy URL, e.g. ``postgresql+psycopg://...``) selects the
  database. It is never logged.
- Without it the tests are skipped, unless ``INAI_REQUIRE_DB=1`` is set (as in CI), in which case
  they fail, so a missing database can never look like a pass.
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from alembic import command
from sqlalchemy import Engine, create_engine, text

from tests.db.support import Db, quoted


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = os.environ.get("INAI_TEST_DATABASE_URL")
    if not url:
        if os.environ.get("INAI_REQUIRE_DB") == "1":
            pytest.fail("INAI_REQUIRE_DB=1 but INAI_TEST_DATABASE_URL is not set")
        pytest.skip("INAI_TEST_DATABASE_URL not set; PostgreSQL schema tests skipped")
    eng = create_engine(url)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Db]:
    schema = f"t12_{uuid.uuid4().hex}"
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA {quoted(schema)}"))
        conn.execute(text(f"SET search_path TO {quoted(schema)}"))
        conn.commit()
        helper = Db(conn, schema)
        command.upgrade(helper.alembic, "head")
        conn.commit()
        try:
            yield helper
        finally:
            conn.rollback()
            conn.execute(text(f"DROP SCHEMA {quoted(schema)} CASCADE"))
            conn.commit()

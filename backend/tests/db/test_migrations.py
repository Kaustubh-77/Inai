"""Migration and rollback tests, plus model/schema parity (T1.2)."""

from alembic import command
from sqlalchemy import inspect

from inai_backend.db import models as _models  # noqa: F401  (registers tables)
from inai_backend.db.base import Base
from tests.db.support import Db

EXPECTED_TABLES = {
    "users",
    "user_settings",
    "consent_records",
    "day_sessions",
    "conversations",
    "transcript_messages",
    "transcript_bookmarks",
    "capture_gaps",
    "session_events",
    "stream_checkpoints",
    "sync_tombstones",
    "processed_operations",
}


def _tables(db: Db) -> set[str]:
    return set(inspect(db.conn).get_table_names(schema=db.schema))


def test_upgrade_creates_all_tables(db: Db) -> None:
    assert _tables(db) == EXPECTED_TABLES | {"alembic_version"}


def test_models_declare_exactly_the_migrated_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_downgrade_to_base_removes_everything_and_upgrade_again_works(db: Db) -> None:
    command.downgrade(db.alembic, "base")
    db.conn.commit()
    assert _tables(db) == {"alembic_version"}
    functions = db.scalar(
        "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
        " WHERE n.nspname = :s",
        s=db.schema,
    )
    assert functions == 0

    command.upgrade(db.alembic, "head")
    db.conn.commit()
    assert _tables(db) == EXPECTED_TABLES | {"alembic_version"}


def test_model_columns_match_migrated_columns(db: Db) -> None:
    inspector = inspect(db.conn)
    for name, table in Base.metadata.tables.items():
        migrated = {c["name"]: c["nullable"] for c in inspector.get_columns(name, schema=db.schema)}
        declared = {c.name: c.nullable for c in table.columns}
        assert declared == migrated, f"column mismatch in {name}"


def test_no_column_can_hold_audio(db: Db) -> None:
    # Product rule: no raw audio anywhere. A binary column would be the obvious place for it.
    count = db.scalar(
        "SELECT count(*) FROM information_schema.columns"
        " WHERE table_schema = :s AND data_type = 'bytea'",
        s=db.schema,
    )
    assert count == 0

"""Trigger and constraint tests for the initial schema (T1.2)."""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError

from tests.db.support import NOW, Db


@contextmanager
def rejected(db: Db, error: type[DBAPIError] = IntegrityError) -> Iterator[None]:
    """Assert the statements inside are rejected, without aborting the outer transaction."""
    with pytest.raises(error), db.conn.begin_nested():
        yield


# --- transcript_messages: original_text is immutable, edits are separate -----------------


def test_original_text_cannot_be_updated(db: Db) -> None:
    user = db.user()
    msg = db.message(user, db.conversation(user), original_text="original")
    with rejected(db):
        db.execute("UPDATE transcript_messages SET original_text = 'changed' WHERE id = :m", m=msg)
    assert db.scalar("SELECT original_text FROM transcript_messages WHERE id = :m", m=msg) == (
        "original"
    )


@pytest.mark.parametrize(
    "assignment",
    [
        "source_stream_id = gen_random_uuid()",
        "source_event_key = 'other'",
    ],
)
def test_dedup_identity_cannot_be_updated(db: Db, assignment: str) -> None:
    user = db.user()
    msg = db.message(user, db.conversation(user))
    with rejected(db):
        db.execute(f"UPDATE transcript_messages SET {assignment} WHERE id = :m", m=msg)  # noqa: S608


def test_owner_of_message_cannot_be_changed(db: Db) -> None:
    user, other = db.user(), db.user()
    msg = db.message(user, db.conversation(user))
    with rejected(db):
        db.execute("UPDATE transcript_messages SET user_id = :o WHERE id = :m", o=other, m=msg)


def test_edit_is_stored_separately_and_revert_restores_original(db: Db) -> None:
    user = db.user()
    msg = db.message(user, db.conversation(user), original_text="original")

    db.execute(
        "UPDATE transcript_messages SET edited_text = 'corrected', edited_at = :t WHERE id = :m",
        t=NOW,
        m=msg,
    )
    row = db.conn.exec_driver_sql(
        "SELECT original_text, edited_text, display_text FROM transcript_messages WHERE id = %s",
        (msg,),
    ).one()
    assert tuple(row) == ("original", "corrected", "corrected")

    db.execute("UPDATE transcript_messages SET edited_text = NULL WHERE id = :m", m=msg)
    assert db.scalar("SELECT display_text FROM transcript_messages WHERE id = :m", m=msg) == (
        "original"
    )


def test_empty_edit_is_rejected(db: Db) -> None:
    user = db.user()
    msg = db.message(user, db.conversation(user))
    with rejected(db):
        db.execute("UPDATE transcript_messages SET edited_text = '' WHERE id = :m", m=msg)


def test_display_text_cannot_be_written_directly(db: Db) -> None:
    user = db.user()
    msg = db.message(user, db.conversation(user))
    with rejected(db, DBAPIError):
        db.execute("UPDATE transcript_messages SET display_text = 'x' WHERE id = :m", m=msg)


def test_unknown_timestamp_source_is_rejected(db: Db) -> None:
    user = db.user()
    conv = db.conversation(user)
    with rejected(db):
        db.message(user, conv, timestamp_source="guessed")


# --- de-duplication identity ---------------------------------------------------------------


def test_duplicate_final_for_same_stream_event_is_rejected(db: Db) -> None:
    user = db.user()
    conv = db.conversation(user)
    stream = uuid.uuid4()
    db.message(user, conv, stream_id=stream, event_key="final-7")
    with rejected(db):
        db.message(user, conv, stream_id=stream, event_key="final-7")


def test_dedup_identity_is_independent_of_conversation(db: Db) -> None:
    # Split/merge never remap event keys, so a retried final must collide even if routed
    # to a different conversation.
    user = db.user()
    stream = uuid.uuid4()
    db.message(user, db.conversation(user), stream_id=stream, event_key="final-1")
    with rejected(db):
        db.message(user, db.conversation(user), stream_id=stream, event_key="final-1")


def test_same_stream_event_for_different_users_is_allowed(db: Db) -> None:
    stream = uuid.uuid4()
    for _ in range(2):
        user = db.user()
        db.message(user, db.conversation(user), stream_id=stream, event_key="final-1")


# --- composite ownership -------------------------------------------------------------------


def test_message_cannot_reference_another_users_conversation(db: Db) -> None:
    owner, intruder = db.user(), db.user()
    conv = db.conversation(owner)
    with rejected(db):
        db.message(intruder, conv)


def test_bookmark_cannot_reference_another_users_message(db: Db) -> None:
    owner, intruder = db.user(), db.user()
    msg = db.message(owner, db.conversation(owner))
    with rejected(db):
        db.execute(
            "INSERT INTO transcript_bookmarks (user_id, transcript_message_id, sync_rev)"
            " VALUES (:u, :m, 1)",
            u=intruder,
            m=msg,
        )


def test_conversation_cannot_join_another_users_day_session(db: Db) -> None:
    owner, intruder = db.user(), db.user()
    day = db.day_session(owner)
    with rejected(db):
        db.conversation(intruder, source="auto_segment", day_session_id=day, segment_order=1)


def test_checkpoint_cannot_route_to_another_users_conversation(db: Db) -> None:
    owner, intruder = db.user(), db.user()
    conv = db.conversation(owner)
    with rejected(db):
        db.checkpoint(intruder, conversation_id=conv)


# --- conversations -------------------------------------------------------------------------


def test_specific_conversation_is_standalone_with_its_own_local_date(db: Db) -> None:
    user = db.user()
    conv = db.conversation(user)
    row = db.conn.exec_driver_sql(
        "SELECT day_session_id, local_date, timezone FROM conversations WHERE id = %s", (conv,)
    ).one()
    assert tuple(row) == (None, NOW.date(), "Asia/Kolkata")


def test_specific_conversation_cannot_belong_to_a_day_session(db: Db) -> None:
    user = db.user()
    day = db.day_session(user)
    with rejected(db):
        db.conversation(user, source="specific", day_session_id=day)


def test_segment_conversation_requires_a_day_session(db: Db) -> None:
    user = db.user()
    with rejected(db):
        db.conversation(user, source="auto_segment")


# --- one active stream per user (A11) ------------------------------------------------------


@pytest.mark.parametrize("holding", ["active", "paused", "reconnect_pending"])
def test_second_slot_holding_stream_is_rejected(db: Db, holding: str) -> None:
    user = db.user()
    db.checkpoint(user, status=holding)
    with rejected(db):
        db.checkpoint(user, status="active")


@pytest.mark.parametrize("released", ["ended", "expired"])
def test_released_stream_frees_the_slot(db: Db, released: str) -> None:
    user = db.user()
    db.checkpoint(user, status=released)
    db.checkpoint(user, status="active")


def test_different_users_can_each_hold_a_stream(db: Db) -> None:
    db.checkpoint(db.user(), status="active")
    db.checkpoint(db.user(), status="active")


# --- capture gaps and stream checkpoints ---------------------------------------------------


def _gap(db: Db, user: uuid.UUID, stream: uuid.UUID, *, ended_offset_s: int = 5) -> None:
    db.execute(
        "INSERT INTO capture_gaps (user_id, source_stream_id, reason, reported_by,"
        " client_start, started_at, ended_at, sync_rev)"
        " VALUES (:u, :s, 'network_loss', 'client', :t, :t,"
        " :t + make_interval(secs => :off), 1)",
        u=user,
        s=stream,
        t=NOW,
        off=ended_offset_s,
    )


def test_gap_must_reference_an_existing_stream_of_the_same_user(db: Db) -> None:
    owner, intruder = db.user(), db.user()
    stream = db.checkpoint(owner, status="ended")
    with rejected(db):
        _gap(db, intruder, stream)


def test_gap_end_must_be_after_start(db: Db) -> None:
    user = db.user()
    stream = db.checkpoint(user, status="ended")
    with rejected(db):
        _gap(db, user, stream, ended_offset_s=0)


def test_checkpoint_with_gap_history_cannot_be_deleted_alone(db: Db) -> None:
    user = db.user()
    stream = db.checkpoint(user, status="ended")
    _gap(db, user, stream)
    with rejected(db):
        db.execute(
            "DELETE FROM stream_checkpoints WHERE user_id = :u AND client_stream_id = :s",
            u=user,
            s=stream,
        )


def test_deleting_conversation_keeps_checkpoint_and_clears_only_routing(db: Db) -> None:
    user = db.user()
    conv = db.conversation(user)
    stream = db.checkpoint(user, status="ended", conversation_id=conv)
    db.execute("DELETE FROM conversations WHERE id = :c", c=conv)
    row = db.conn.exec_driver_sql(
        "SELECT user_id, conversation_id FROM stream_checkpoints WHERE client_stream_id = %s",
        (stream,),
    ).one()
    assert tuple(row) == (user, None)


# --- account deletion ----------------------------------------------------------------------


def test_deleting_a_user_removes_all_of_their_data_only(db: Db) -> None:
    user, other = db.user(), db.user()
    for owner in (user, other):
        conv = db.conversation(owner)
        msg = db.message(owner, conv)
        db.execute(
            "INSERT INTO transcript_bookmarks (user_id, transcript_message_id, sync_rev)"
            " VALUES (:u, :m, 1)",
            u=owner,
            m=msg,
        )
        stream = db.checkpoint(owner, status="ended", conversation_id=conv)
        _gap(db, owner, stream)

    db.execute("DELETE FROM users WHERE id = :u", u=user)

    for table in (
        "conversations",
        "transcript_messages",
        "transcript_bookmarks",
        "stream_checkpoints",
        "capture_gaps",
    ):
        remaining = db.scalar(
            f"SELECT count(*) FROM {table} WHERE user_id = :u",  # noqa: S608 (fixed table names)
            u=user,
        )
        assert remaining == 0, table
        kept = db.scalar(f"SELECT count(*) FROM {table} WHERE user_id = :u", u=other)  # noqa: S608
        assert kept == 1, table

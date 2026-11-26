"""ORM models for the Inai MVP schema (design.md section 14, task T1.2).

Constraints that protect data integrity (immutability trigger, CHECKs, the one-active-stream
partial index, composite ownership foreign keys) are created by the migrations. The models
declare columns, primary keys and the composite foreign keys used for ownership, so that
repositories can be written against them.

Rules that the models must never weaken:
- ``original_text`` is immutable; corrections go to ``edited_text`` (nullable).
- Partial captions and audio are never stored. There is no audio column anywhere.
- Every user-owned row carries ``user_id`` and references parents by ``(id, user_id)``.
"""

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from inai_backend.db.base import Base

_NOW = text("now()")
_GEN_UUID = text("gen_random_uuid()")


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=_GEN_UUID)


def _user_fk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


def _tstz(*, nullable: bool, default_now: bool = False) -> Mapped[Any]:
    return mapped_column(
        DateTime(timezone=True),
        nullable=nullable,
        server_default=_NOW if default_now else None,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _pk()
    auth_subject: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'Asia/Kolkata'")
    )
    sync_counter: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    created_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_language: Mapped[str | None] = mapped_column(Text)
    ui_locale: Mapped[str | None] = mapped_column(Text)
    font_scale: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="1.00"
    )
    high_contrast: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    auto_segmentation_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    silence_threshold_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="2000"
    )
    updated_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    consent_type: Mapped[str] = mapped_column(Text, nullable=False)
    notice_version: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str | None] = mapped_column(Text)
    accepted_at: Mapped[dt.datetime] = _tstz(nullable=False)


class DaySession(Base):
    __tablename__ = "day_sessions"
    __table_args__ = (UniqueConstraint("id", "user_id"),)

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    local_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'full_day_hybrid'")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[dt.datetime] = _tstz(nullable=False)
    ended_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    sync_rev: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)
    created_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        ForeignKeyConstraint(
            ["day_session_id", "user_id"],
            ["day_sessions.id", "day_sessions.user_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("day_session_id", "segment_order", deferrable=True, initially="DEFERRED"),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    day_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    local_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    language_hint: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[dt.datetime] = _tstz(nullable=False)
    ended_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    segment_order: Mapped[int | None] = mapped_column(Integer)
    sync_rev: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)
    created_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class TranscriptMessage(Base):
    __tablename__ = "transcript_messages"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        UniqueConstraint("user_id", "source_stream_id", "source_event_key"),
        ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["conversations.id", "conversations.user_id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_stream_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_event_key: Mapped[str] = mapped_column(Text, nullable=False)
    speaker_label: Mapped[str | None] = mapped_column(Text)
    # Immutable after insert (enforced by trigger). Never assign to this on an existing row.
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    edited_text: Mapped[str | None] = mapped_column(Text)
    edited_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    display_text: Mapped[str] = mapped_column(
        Text,
        Computed("COALESCE(edited_text, original_text)", persisted=True),
        # Matches the migration: the generated column carries no NOT NULL constraint.
        # It is never NULL in practice because original_text is NOT NULL.
        nullable=True,
    )
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    search_norm_version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    original_language: Mapped[str | None] = mapped_column(Text)
    provider_locale: Mapped[str | None] = mapped_column(Text)
    translated_text: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    ended_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    timestamp_source: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    sequence_number: Mapped[int | None] = mapped_column(BigInteger)
    sync_rev: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)
    created_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class TranscriptBookmark(Base):
    __tablename__ = "transcript_bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "transcript_message_id"),
        ForeignKeyConstraint(
            ["transcript_message_id", "user_id"],
            ["transcript_messages.id", "transcript_messages.user_id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    transcript_message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    sync_rev: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class StreamCheckpoint(Base):
    """Stream metadata only (IDs, sequence numbers, timing). Never audio."""

    __tablename__ = "stream_checkpoints"
    __table_args__ = (
        UniqueConstraint("user_id", "client_stream_id"),
        ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["conversations.id", "conversations.user_id"],
            # Column-list form (PostgreSQL 15+): clears only the routing target and keeps
            # user_id, matching the migration.
            ondelete="SET NULL (conversation_id)",
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    client_stream_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    last_accepted_sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default="0"
    )
    anchor_utc: Mapped[dt.datetime | None] = _tstz(nullable=True)
    clock_skew_ms: Mapped[int | None] = mapped_column(Integer)
    provider_id: Mapped[str | None] = mapped_column(Text)
    provider_locale: Mapped[str | None] = mapped_column(Text)
    provider_session_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(Text, nullable=False)
    grace_expires_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    paused_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    ended_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class CaptureGap(Base):
    __tablename__ = "capture_gaps"
    __table_args__ = (
        UniqueConstraint("user_id", "client_gap_id"),
        UniqueConstraint("user_id", "source_stream_id", "server_gap_key"),
        ForeignKeyConstraint(
            ["day_session_id", "user_id"],
            ["day_sessions.id", "day_sessions.user_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["conversations.id", "conversations.user_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["user_id", "source_stream_id"],
            ["stream_checkpoints.user_id", "stream_checkpoints.client_stream_id"],
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    source_stream_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    day_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    client_gap_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    server_gap_key: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reported_by: Mapped[str] = mapped_column(Text, nullable=False)
    client_start: Mapped[dt.datetime | None] = _tstz(nullable=True)
    client_end: Mapped[dt.datetime | None] = _tstz(nullable=True)
    server_start_bound: Mapped[dt.datetime | None] = _tstz(nullable=True)
    server_end_bound: Mapped[dt.datetime | None] = _tstz(nullable=True)
    started_at: Mapped[dt.datetime] = _tstz(nullable=False)
    start_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    ended_at: Mapped[dt.datetime | None] = _tstz(nullable=True)
    end_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sync_rev: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)
    updated_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class SessionEvent(Base):
    __tablename__ = "session_events"
    __table_args__ = (
        UniqueConstraint("user_id", "client_event_id"),
        ForeignKeyConstraint(
            ["day_session_id", "user_id"],
            ["day_sessions.id", "day_sessions.user_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["conversation_id", "user_id"],
            ["conversations.id", "conversations.user_id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _user_fk()
    day_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    client_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[dt.datetime] = _tstz(nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class SyncTombstone(Base):
    """Content-free deletion marker for sync. Holds IDs only, never transcript text."""

    __tablename__ = "sync_tombstones"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    entity_type: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    merged_into_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    sync_rev: Mapped[int] = mapped_column(BigInteger, nullable=False)
    deleted_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)


class ProcessedOperation(Base):
    """Idempotency record for mutating requests and queued offline operations."""

    __tablename__ = "processed_operations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    op_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    response_status: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    processed_at: Mapped[dt.datetime] = _tstz(nullable=False, default_now=True)

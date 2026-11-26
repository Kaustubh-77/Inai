"""Initial schema (T1.2): users, sessions, conversations, transcripts, gaps, streams, sync.

Follows design.md section 14. Differences from the illustrative DDL, all deliberate:
- No ``CREATE EXTENSION pgcrypto``: ``gen_random_uuid()`` is built into PostgreSQL 13+, and the
  project targets PostgreSQL 16, so no extension (and no extension privilege) is needed.
- The immutability trigger also protects ``user_id``, because the de-duplication identity
  ``(user_id, source_stream_id, source_event_key)`` must be immutable as a whole.
- No search indexes: ``pg_trgm`` and any search index wait for the T1.1 search spike.
- ``capture_gaps`` is created after ``stream_checkpoints`` so ``fk_gap_source_stream`` is declared
  inline instead of with a later ``ALTER TABLE``. The constraint itself is unchanged.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UPGRADE = [
    """
    CREATE TABLE users (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     auth_subject TEXT NOT NULL UNIQUE,
     email TEXT,
     display_name TEXT,
     timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
     sync_counter BIGINT NOT NULL DEFAULT 0,
     created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE user_settings (
     user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
     preferred_language TEXT,
     ui_locale TEXT,
     font_scale NUMERIC(3,2) NOT NULL DEFAULT 1.00,
     high_contrast BOOLEAN NOT NULL DEFAULT false,
     auto_segmentation_enabled BOOLEAN NOT NULL DEFAULT true,
     silence_threshold_ms INTEGER NOT NULL DEFAULT 2000,
     updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE consent_records (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     consent_type TEXT NOT NULL,
     notice_version TEXT NOT NULL,
     locale TEXT,
     accepted_at TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE day_sessions (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     local_date DATE NOT NULL,
     timezone TEXT NOT NULL,
     mode TEXT NOT NULL DEFAULT 'full_day_hybrid' CHECK (mode IN ('full_day_hybrid')),
     status TEXT NOT NULL CHECK (status IN ('active','paused','completed','interrupted')),
     started_at TIMESTAMPTZ NOT NULL,
     ended_at TIMESTAMPTZ,
     sync_rev BIGINT NOT NULL,
     updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     UNIQUE (id, user_id)
    )
    """,
    "CREATE INDEX idx_day_user_date ON day_sessions(user_id, local_date DESC)",
    "CREATE INDEX idx_day_sync ON day_sessions(user_id, sync_rev)",
    """
    CREATE TABLE conversations (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     day_session_id UUID,
     local_date DATE NOT NULL,
     timezone TEXT NOT NULL,
     title TEXT,
     source TEXT NOT NULL CHECK (source IN ('specific','auto_segment','manual_segment')),
     status TEXT NOT NULL CHECK (status IN ('active','paused','completed','interrupted')),
     language_hint TEXT,
     started_at TIMESTAMPTZ NOT NULL,
     ended_at TIMESTAMPTZ,
     segment_order INTEGER,
     sync_rev BIGINT NOT NULL,
     updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     UNIQUE (id, user_id),
     FOREIGN KEY (day_session_id, user_id)
       REFERENCES day_sessions(id, user_id) ON DELETE CASCADE,
     CHECK ((source = 'specific' AND day_session_id IS NULL)
         OR (source <> 'specific' AND day_session_id IS NOT NULL)),
     UNIQUE (day_session_id, segment_order) DEFERRABLE INITIALLY DEFERRED
    )
    """,
    "CREATE INDEX idx_conv_user_date ON conversations(user_id, local_date DESC)",
    "CREATE INDEX idx_conv_sync ON conversations(user_id, sync_rev)",
    """
    CREATE TABLE transcript_messages (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     conversation_id UUID NOT NULL,
     source_stream_id UUID NOT NULL,
     source_event_key TEXT NOT NULL,
     speaker_label TEXT,
     original_text TEXT NOT NULL,
     edited_text TEXT,
     edited_at TIMESTAMPTZ,
     display_text TEXT GENERATED ALWAYS AS (COALESCE(edited_text, original_text)) STORED,
     search_text TEXT NOT NULL,
     search_norm_version SMALLINT NOT NULL,
     original_language TEXT,
     provider_locale TEXT,
     translated_text TEXT,
     started_at TIMESTAMPTZ,
     ended_at TIMESTAMPTZ,
     timestamp_source TEXT NOT NULL
       CHECK (timestamp_source IN ('provider_offsets','chunk_bracketed','server_received')),
     confidence NUMERIC(5,4),
     sequence_number BIGINT,
     sync_rev BIGINT NOT NULL,
     updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     UNIQUE (id, user_id),
     UNIQUE (user_id, source_stream_id, source_event_key),
     FOREIGN KEY (conversation_id, user_id)
       REFERENCES conversations(id, user_id) ON DELETE CASCADE,
     CHECK (edited_text IS NULL OR length(edited_text) > 0)
    )
    """,
    """
    CREATE INDEX idx_msg_conv_time
     ON transcript_messages(conversation_id, started_at, source_stream_id, sequence_number)
    """,
    "CREATE INDEX idx_msg_sync ON transcript_messages(user_id, sync_rev)",
    """
    CREATE FUNCTION transcript_messages_guard_immutable() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.original_text IS DISTINCT FROM OLD.original_text
         OR NEW.user_id IS DISTINCT FROM OLD.user_id
         OR NEW.source_stream_id IS DISTINCT FROM OLD.source_stream_id
         OR NEW.source_event_key IS DISTINCT FROM OLD.source_event_key THEN
        RAISE EXCEPTION 'transcript_messages identity and original_text are immutable'
          USING ERRCODE = 'check_violation';
      END IF;
      RETURN NEW;
    END
    $$
    """,
    """
    CREATE TRIGGER transcript_messages_immutable
     BEFORE UPDATE ON transcript_messages
     FOR EACH ROW EXECUTE FUNCTION transcript_messages_guard_immutable()
    """,
    """
    CREATE TABLE transcript_bookmarks (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     transcript_message_id UUID NOT NULL,
     note TEXT,
     sync_rev BIGINT NOT NULL,
     created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     UNIQUE (user_id, transcript_message_id),
     FOREIGN KEY (transcript_message_id, user_id)
       REFERENCES transcript_messages(id, user_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE stream_checkpoints (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     conversation_id UUID,
     client_stream_id UUID NOT NULL,
     last_accepted_sequence BIGINT NOT NULL DEFAULT 0,
     anchor_utc TIMESTAMPTZ,
     clock_skew_ms INTEGER,
     provider_id TEXT,
     provider_locale TEXT,
     provider_session_count INTEGER NOT NULL DEFAULT 0,
     status TEXT NOT NULL
       CHECK (status IN ('active','paused','reconnect_pending','expired','ended')),
     grace_expires_at TIMESTAMPTZ,
     paused_at TIMESTAMPTZ,
     ended_reason TEXT CHECK (ended_reason IN ('user_stop','remote_user_end','day_session_end')),
     updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     UNIQUE (user_id, client_stream_id),
     FOREIGN KEY (conversation_id, user_id)
       REFERENCES conversations(id, user_id) ON DELETE SET NULL (conversation_id)
    )
    """,
    """
    CREATE UNIQUE INDEX one_active_stream_per_user ON stream_checkpoints (user_id)
     WHERE status IN ('active','paused','reconnect_pending')
    """,
    """
    CREATE TABLE capture_gaps (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     source_stream_id UUID NOT NULL,
     day_session_id UUID,
     conversation_id UUID,
     client_gap_id UUID,
     server_gap_key TEXT,
     reason TEXT NOT NULL CHECK (reason IN (
       'os_interruption','network_loss','provider_error','provider_throttle',
       'permission_revoked','route_change','process_terminated','auth_expired',
       'rotation_uncertain','unknown')),
     reported_by TEXT NOT NULL CHECK (reported_by IN ('client','server','both')),
     client_start TIMESTAMPTZ,
     client_end TIMESTAMPTZ,
     server_start_bound TIMESTAMPTZ,
     server_end_bound TIMESTAMPTZ,
     started_at TIMESTAMPTZ NOT NULL,
     start_estimated BOOLEAN NOT NULL DEFAULT false,
     ended_at TIMESTAMPTZ,
     end_estimated BOOLEAN NOT NULL DEFAULT false,
     sync_rev BIGINT NOT NULL,
     created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     CHECK (client_start IS NOT NULL OR server_start_bound IS NOT NULL),
     CHECK (ended_at IS NULL OR ended_at > started_at),
     UNIQUE (user_id, client_gap_id),
     UNIQUE (user_id, source_stream_id, server_gap_key),
     FOREIGN KEY (day_session_id, user_id)
       REFERENCES day_sessions(id, user_id) ON DELETE CASCADE,
     FOREIGN KEY (conversation_id, user_id)
       REFERENCES conversations(id, user_id) ON DELETE CASCADE,
     CONSTRAINT fk_gap_source_stream FOREIGN KEY (user_id, source_stream_id)
       REFERENCES stream_checkpoints (user_id, client_stream_id) ON DELETE NO ACTION
    )
    """,
    "CREATE INDEX idx_gap_day ON capture_gaps(user_id, started_at)",
    "CREATE INDEX idx_gap_stream ON capture_gaps(user_id, source_stream_id, started_at)",
    """
    CREATE TABLE session_events (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     day_session_id UUID,
     conversation_id UUID,
     client_event_id UUID,
     event_type TEXT NOT NULL,
     occurred_at TIMESTAMPTZ NOT NULL,
     metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
     UNIQUE (user_id, client_event_id),
     FOREIGN KEY (day_session_id, user_id)
       REFERENCES day_sessions(id, user_id) ON DELETE CASCADE,
     FOREIGN KEY (conversation_id, user_id)
       REFERENCES conversations(id, user_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE sync_tombstones (
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     entity_type TEXT NOT NULL,
     entity_id UUID NOT NULL,
     merged_into_id UUID,
     sync_rev BIGINT NOT NULL,
     deleted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     PRIMARY KEY (user_id, entity_type, entity_id)
    )
    """,
    "CREATE INDEX idx_tomb_sync ON sync_tombstones(user_id, sync_rev)",
    """
    CREATE TABLE processed_operations (
     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     op_id UUID NOT NULL,
     response_status SMALLINT NOT NULL,
     processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     PRIMARY KEY (user_id, op_id)
    )
    """,
]

# Reverse dependency order. capture_gaps goes before stream_checkpoints because of
# fk_gap_source_stream (NO ACTION).
_DOWNGRADE = [
    "DROP TABLE processed_operations",
    "DROP TABLE sync_tombstones",
    "DROP TABLE session_events",
    "DROP TABLE capture_gaps",
    "DROP TABLE stream_checkpoints",
    "DROP TABLE transcript_bookmarks",
    "DROP TABLE transcript_messages",
    "DROP FUNCTION transcript_messages_guard_immutable()",
    "DROP TABLE conversations",
    "DROP TABLE day_sessions",
    "DROP TABLE consent_records",
    "DROP TABLE user_settings",
    "DROP TABLE users",
]


def upgrade() -> None:
    for statement in _UPGRADE:
        op.execute(statement)


def downgrade() -> None:
    for statement in _DOWNGRADE:
        op.execute(statement)

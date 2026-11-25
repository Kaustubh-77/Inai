# Inai MVP — Design

Items marked **[Approved Ax]** are amendment decisions approved by the owner on 2026-11-25 (A1–A14). Items marked **[Unverified]** depend on the validation gate (T0.2). Numeric values marked "config" are placeholders to be set by measurement, not commitments.

## 1. Architecture
React Native + TypeScript shared app (UI, presentation, local store, sync). Kotlin (Android) and Swift (iOS) native audio engines own capture, VAD, chunking, replay buffer and the WebSocket transport. FastAPI backend with Firebase ID token verification, a provider-neutral ASR adapter, and PostgreSQL persistence. SQLite on device for offline use. No ASR provider is selected; Sarvam AI is the first candidate to evaluate.

```
Mic → Native engine [capture → VAD → chunker → replay buffer → WS client]
                                   │ state/transcript events only
                                   ▼
                          React Native (UI, SQLite, sync) ──REST──► FastAPI ──► PostgreSQL
Native WS client ───────────── TLS WebSocket ─────────────────────► FastAPI ──► ASR adapter ──► provider
```

## 2. Mobile components
- Home: Start My Day, Start Conversation, today's sessions.
- Sign-in and consent screens.
- Recording: large captions, language, elapsed time, recording state, pause/resume/stop, connectivity and gap indicators.
- Day history: group by stored local date/timezone (days and standalone conversations).
- Conversation detail: timestamped chat-like transcript with gap markers, edit/revert, bookmark, conflict resolution.
- Settings: verified languages, caption size, contrast, segmentation preferences, UI locale, account deletion.
- RecordingController: UI projection of native engine state plus UI-only states.
- NativeEngineBridge: typed interface to the platform engine (no audio).
- LocalStore and SyncEngine: SQLite access, pending queue, pull/push.
- API client: authenticated REST with idempotency keys.

## 3. Native engine
### Common responsibilities
Capture, VAD, chunking, bounded in-memory replay buffer, WebSocket transport with reconnect, capture-gap detection, authoritative capture and stream state. Audio is never written to disk and never sent to JS. The engine keeps running if JS is suspended; JS re-attaches with `getEngineStatus()`.

### Android
Kotlin engine and user-initiated foreground service with the microphone type, `RECORD_AUDIO`, `FOREGROUND_SERVICE_MICROPHONE` and `POST_NOTIFICATIONS` as required by the target SDK. The microphone is a while-in-use permission, so capture can only start from a visible user-initiated state; it cannot be (re)started from the background after an interruption. Handle permission revocation, microphone privacy toggle, persistent notification, audio focus, route changes, process/lifecycle recovery, OEM battery limits and service failure. Android 15/16 specifics and Play declarations are **[Unverified]**.

### iOS
Swift engine using AVAudioSession and AVAudioEngine or justified equivalent. Handle permission, session activation, interruptions, route changes, reactivation and permitted background behaviour. Background mode, App Review justification and suspension behaviour are **[Unverified]**. Do not imply unrestricted background recording.

### Shared interface
- `requestPermission()`, `getPermissionState()`, `getPlatformCapabilities()`
- `configureEngine(config)` (endpoints, VAD config, replay window; no secrets), `getEngineStatus()`
- `startCapture({mode, daySessionId?, conversationId?, language, clientStreamId})`, `pauseCapture()`, `resumeCapture()`, `stopCapture()`, `requestNewConversation()`
- `updateAuthToken(token)` fallback path
- `subscribeToStateChanges()` and `subscribeToStreamEvents()`

Capabilities include whether automatic resume after interruption is possible. `language` is an app code; the server resolves the provider locale.

### Token access from native **[Approved A1; Unverified]**
Preferred: the native engine obtains ID tokens from the platform Firebase SDK session shared with the JS Firebase package, so background refresh does not need JS. Verification task: T0.2. Fallback: JS calls `updateAuthToken` while foregrounded; a stream that outlives its token ends with an `auth_expired` gap and the user is alerted.

## 4. State machine
Native engine is authoritative for capture and stream state. The JS RecordingController mirrors it and adds UI-only states.

Capture states: `idle`, `ready`, `recording_specific`, `recording_day`, `paused`, `stopping`, `stopped`, `interrupted`, `error`. UI-only states: `requesting_permission`, `saved`.

Stream status is orthogonal: `connecting`, `authenticated`, `streaming`, `reconnecting`, `offline`, `closed`.

Rules:
- `paused` is user-initiated only. An OS interruption must never be represented as a user pause; it yields `interrupted` and opens a capture gap.
- `interrupted` carries cause and `canResumeAutomatically`. When false, the user must act (for example on Android background restrictions).
- Network loss does not change the capture state; stream status goes to `reconnecting`/`offline`, and a gap opens once the replay window is exceeded.
- Preserve the last confirmed transcript sequence.
- Valid transitions are unit-tested in both native and JS layers (T3.3, T4.x).

## 5. Language catalog and provider locale mapping **[Approved A9]**
A versioned server-side configuration (schema-validated, changed through reviewed commits) lists languages:

| Field | Meaning |
|---|---|
| `app_code` | `ta`, `te`, `kn`, `ml`, `hi`, `en` |
| `display_name_native` / `display_name_en` | Selector labels |
| `provider_id` | Adapter identifier |
| `provider_locale` | Provider-specific locale, empty until verified |
| `status` | `unverified`, `verified_streaming`, `verified_limited`, `unsupported` |
| `evidence_ref` | Link or ID into `docs/architecture/platform-provider-validation.md` |
| `verified_at`, `region` | When and where verified |
| `limitations` | Known caveats shown to users when `verified_limited` |

- `GET /v1/languages` returns only `verified_streaming` and `verified_limited` entries for the active provider and region.
- A language is never hard-coded in the apps. `user_settings.preferred_language` is nullable and unset by default. If the stored preference becomes unverified, the user is asked to choose again.
- Messages store the app code in `original_language` and the provider-returned locale in `provider_locale`.
- Mapping `en` to a specific provider English locale is decided only from verified evidence.

## 6. Local store (SQLite)
Purpose: offline reading, search and editing of previously synchronised data, plus pending operations. Server remains the source of truth.

Tables (local names mirror server entities):
- `day_sessions`, `conversations`, `transcript_messages` (with `original_text`, `edited_text`, `search_text`, `sync_status`), `transcript_bookmarks`, `capture_gaps`: mirrors of server rows including `sync_rev`.
- `pending_ops`: `op_id` (UUID, also the `Idempotency-Key`), `entity_type`, `entity_id`, `op_type`, `payload`, `expected_value`, `created_at`, `attempts`, `status` (`queued`, `in_flight`, `failed`, `conflict`).
- `conflicts`: `entity_type`, `entity_id`, `field`, `local_value`, `server_value`, `detected_at`.
- `sync_state`: `cursor`, `last_full_sync_at`, `schema_version`.
- `meta`: store version, user subject.

Rules:
- Versioned forward-only migrations with automated tests. A store that fails to open or migrate is rebuilt from the server after warning about unsynchronised edits.
- Encrypted at rest with a key in Keychain/Keystore **[Approved A2]**; excluded from backups; wiped on sign-out and account deletion **[Approved A12]**.
- Never stores audio, partial captions or tokens.
- Library selection (encryption, FTS tokenizer, React Native New Architecture support) is **[Unverified]** and decided in T3.4.
- Local search uses the same normalised `search_text` as the server. Whether SQLite FTS5 tokenizers handle Indic combining marks correctly is **[Unverified]**; a trigram tokenizer or `LIKE` over `search_text` are candidates, selected by the search spike.

## 7. Synchronisation and conflict handling
### Revisions
Each user has a monotonically increasing `sync_counter`. Every write to a synced row increments it within the same transaction (the user row is locked for the update) and stores the value in the row's `sync_rev`. Because the counter is assigned under a per-user lock, commit order equals revision order and a pull cursor cannot skip a later-committed lower revision. Per-user write contention is acceptable at this scale.

### Pull
`GET /v1/sync/changes?cursor=N&limit=` returns changed rows (days, conversations, messages, bookmarks, gaps), tombstones, `next_cursor` and `has_more`. Cursor `0` is a full download. Tombstones are retained for a configured window (config); an older cursor returns `cursor_expired` and the client performs a full resync.

### Deletes and merges
Deleting removes row content immediately (privacy) and writes a content-free row in `sync_tombstones(entity_type, entity_id, sync_rev, merged_into_id)`. A merged conversation produces a tombstone with `merged_into_id`.

### Push
Queued operations are sent in order per entity with `Idempotency-Key = op_id`. The server records `processed_operations(user_id, op_id)` for a retention window (config) and returns the original result for repeats.

### Offline-capable operations **[Approved A3]**
| Operation | Endpoint | Concurrency rule |
|---|---|---|
| Edit message text | `PATCH /v1/transcript-messages/{id}` with `edited_text`, `expected_edited_text` | Compare-and-set |
| Revert edit | same, with `edited_text: null` | Compare-and-set |
| Rename conversation | `PATCH /v1/conversations/{id}` with `title`, `expected_title` | Compare-and-set |
| Add/remove bookmark | `PUT/DELETE .../bookmark` | Idempotent set semantics; note is last-write-wins by server order |

Split, merge, delete and export are online-only.

### Conflict policy **[Approved A4]**
- CAS success: apply, increment `sync_rev`, return the new row.
- CAS mismatch: respond `409` with the current server value. The client:
  - drops the pending operation as already applied if the server value equals the intended value;
  - otherwise stores a `conflicts` row and shows both versions. The user chooses keep mine, keep server, or edit manually. The choice becomes a new operation against the current server value.
- Repeated edits of the same field while offline are coalesced, keeping the first `expected` value.
- Target deleted (`404`/tombstone) or merged: the operation is marked `failed` with a visible reason. For merged conversations the client follows `merged_into_id` for messages, which keep their IDs.
- `401`: pause the queue until re-authentication; never discard operations.
- Permanent validation errors (`4xx` other than 401/404/409): mark `failed` and surface.
- Network errors: exponential backoff.
- Unsynchronised operations are listed to the user before sign-out.

## 8. Audio pipeline, streaming and rotation
Native capture → bounded PCM frames → VAD → chunker → (replay buffer) → authenticated WebSocket → backend ASR adapter → partial/final events → final persistence. Audio is discarded after processing. Do not hard-code the audio format until provider requirements are verified.

### VAD and transmission **[Approved A7]**
- Specific Conversation: stream continuously.
- Full-Day: transmit speech plus pre-roll and post-roll (config). VAD algorithm and thresholds are chosen in T4.1 and evaluated with target users because a false negative drops speech.
- Chunks carry VAD flags so the server can reason about speech activity.

### Replay and acknowledgement **[Approved A8]**
- `audio.ack` is cumulative and means "accepted into the server pipeline", not "recognised".
- Native keeps unacknowledged chunks in a bounded memory-only replay buffer (size by measurement, config). After reconnect the server returns `last_accepted_sequence`, and native replays only chunks after it that are still buffered.
- Chunks that fell out of the window are lost and recorded as a capture gap.
- If a provider session fails while acknowledged audio has no final result, the server records a server-detected gap for that span.

### Provider sessions and rotation
Provider sessions are owned by the server and decoupled from the device socket.
- The adapter exposes capabilities: `max_session_duration_s`, `idle_timeout_s`, `supports_segment_offsets`, `supports_partials`, `audio_formats`. Values are **[Unverified]** and null until validated; none are assumed.
- A provider session opens on the first speech chunk and closes after an idle period (config) or at a planned rotation.
- Planned rotation: when a session approaches its verified limit (minus a safety margin, config) the server waits for a silence boundary within a deadline (config) and opens a new session there. If the deadline is reached, it performs a forced rotation with a short overlap (config).
- Overlap handling: the old session's finals are accepted up to the cutover capture offset, the new session's finals starting before it are dropped, and duplicate text across the cutover is detected by offset and normalised text comparison. If correctness cannot be established, emit `stream.warning` and record a minimal gap rather than guessing.
- Each rotation is logged as a `session_events` row with safe metadata.
- Throttling and provider errors trigger backoff with degraded-state warnings.

### Reconnect
Reconnect uses the same `client_stream_id`. A transport reconnect may start a new provider session; text spanning that boundary can be split across two messages. This is expected and documented.

## 9. Timestamp mapping **[Approved A13]**
1. **Anchor:** `stream.start` carries `anchor_utc_ms` (device wall clock) and a monotonic reading. Every `audio.chunk` has `capture_offset_ms` (monotonic since anchor, including paused periods) and `duration_ms`.
2. **Skew:** the server compares `anchor_utc_ms` with its receive time and stores `clock_skew_ms` in the checkpoint. If skew exceeds a configured threshold, the server-corrected anchor is used and `timestamp_source` reflects that.
3. **Provider mapping:** for each provider session the server keeps a chunk index mapping provider audio time to `capture_offset_ms`, so VAD gating produces correct piecewise mapping.
4. **Message times:** `started_at = anchor_utc + mapped_offset`; `ended_at` likewise. `timestamp_source` is one of `provider_offsets`, `chunk_bracketed` (bracketed by the first and last chunk contributing to the final), or `server_received` (last resort).
5. Whether the provider returns offsets is **[Unverified]**; the design never assumes it.
6. Timestamps are stored as UTC. `local_date` and `timezone` are fixed at session creation and do not change when the device timezone changes.
7. Ordering within a conversation: `(started_at, source_stream_id, sequence_number, id)`.

## 10. Day-session modes, segmentation and split/merge
### Modes
- `full_day_hybrid`: started by Start My Day; VAD suggestions plus manual controls. The only mode in the MVP.
- Removed: `full_day` as a separate value and `mixed`. Reason: `mixed` was undefined and no requirement referenced it. Further modes require a migration and approval.
- `user_settings.auto_segmentation_enabled` controls whether boundaries are applied or only recorded.

### Containment **[Approved A6]**
- A conversation with `source = 'specific'` has no day session. It stores its own `local_date` and `timezone`.
- Conversations with `source` `auto_segment` or `manual_segment` belong to a day session and share its `local_date`.
- Day history lists, for each local date, day sessions with their conversations plus standalone conversations.

### Segmentation
- Native VAD speech start opens a candidate segment.
- Sustained silence (initial test range 1.5–2.5 s, config; default 2 s) proposes a boundary after a grace window.
- Manual New Conversation sends `segment.new`; the next conversation is created on the next accepted speech content.
- The server creates the conversation lazily, so empty segments never exist, and informs the device with `segment.opened`.
- A maximum segment duration is configurable (T6.2).

### Split **[Approved A5]**
- Input: conversation ID and `at_message_id` (the first message of the new conversation).
- Messages with order key greater than or equal to `at_message_id`'s move to a new conversation in the same container. The new conversation's `source` is `specific` for standalone parents and `manual_segment` otherwise.
- Message IDs, `source_stream_id`, `source_event_key`, timestamps and bookmarks do not change.
- Gaps and session events starting at or after the split time move with them; a gap spanning the split time stays with the earlier conversation.
- An active stream pointing at the source is re-pointed to the new conversation if the split point is in the live portion.
- `segment_order` for later conversations in the day is shifted in one transaction.

### Merge **[Approved A5]**
- Allowed within one day session, or between standalone conversations on the same `local_date`.
- The earlier conversation keeps its ID; the later one is deleted with a tombstone carrying `merged_into_id`.
- Messages move, keeping their IDs and keys. Order is by the ordering key in §9.
- Active stream checkpoints pointing at the merged-away conversation are re-pointed to the survivor.
- Titles: survivor's title is kept, and the other title is returned in the response so the client can offer to combine.

### Event-key handling (no remapping required)
Message identity for de-duplication is `(user_id, source_stream_id, source_event_key)`, immutable and independent of the conversation. This replaces the previous `UNIQUE(conversation_id, event_key)`, which could collide on merge. A retried or duplicated final that arrives after a split or merge hits the unique constraint and is ignored. New finals are routed through the stream checkpoint's *current* conversation, which split and merge update. `source_event_key` is generated deterministically by the server (provider session ordinal plus result ordinal).

## 11. REST API
Conventions: cursor pagination, a problem-details error model with stable error codes, `Idempotency-Key` on mutating requests, client-supplied UUIDs allowed for creates (repeat with the same owner returns the existing resource; conflicts with another owner return a generic error). Derive user identity from the verified Firebase principal; never trust a body `user_id`.

| Method/path | Purpose |
|---|---|
| `GET /v1/me` | Profile and provisioning |
| `PUT /v1/me/settings` | Settings |
| `DELETE /v1/me` | Account deletion (server data and Firebase user) |
| `POST /v1/consents` | Record consent acknowledgement |
| `GET /v1/languages` | Verified languages |
| `POST /v1/day-sessions` | Create day |
| `GET /v1/day-sessions?from=&to=` | List days |
| `GET /v1/day-sessions/{id}` | Get day and conversations |
| `POST /v1/day-sessions/{id}/pause` | Pause |
| `POST /v1/day-sessions/{id}/resume` | Resume |
| `POST /v1/day-sessions/{id}/end` | End |
| `POST /v1/conversations` | Create conversation/segment |
| `GET /v1/conversations/{id}` | Fetch transcript including gaps |
| `PATCH /v1/conversations/{id}` | Rename/update (CAS on title) |
| `POST /v1/conversations/{id}/split` | Split |
| `POST /v1/conversations/{id}/merge` | Merge |
| `PATCH /v1/transcript-messages/{id}` | Edit or revert (CAS on `edited_text`) |
| `PUT/DELETE /v1/transcript-messages/{id}/bookmark` | Bookmark |
| `GET /v1/search?q=&from=&to=` | Search |
| `GET /v1/conversations/{id}/export` | Export (displayed text; optional original) |
| `DELETE /v1/conversations/{id}` | Delete conversation |
| `DELETE /v1/day-sessions/{id}` | Delete day |
| `GET /v1/sync/changes?cursor=` | Sync pull |

## 12. WebSocket protocol
Endpoint example: `/v1/stream`. Every message carries `schema_version`, `event_id`, `type`, `stream_id` and `sent_at`; audio chunks add `seq`, `capture_offset_ms`, `duration_ms` and VAD flags. Audio framing (binary frames with a JSON header versus encoded payloads) is decided in T2.1 from the evidence recorded in T0.2 and is not assumed here.

| Direction | Events |
|---|---|
| Client to server | `stream.auth`, `stream.reauth`, `stream.start`, `audio.chunk`, `segment.suggested`, `segment.new`, `stream.pause`, `stream.resume`, `capture.gap`, `stream.end` |
| Server to client | `stream.auth.ok`, `audio.ack`, `transcript.partial`, `transcript.final`, `segment.opened`, `stream.warning`, `stream.closed` |

### Authentication **[Approved A1]**
- The socket opens without credentials. The first message must be `stream.auth` with a Firebase ID token, within a short timeout (config); otherwise the server closes the connection.
- The server verifies the token, derives the user, and replies `stream.auth.ok` with the token expiry.
- Before expiry the client sends `stream.reauth` with a fresh token. If none arrives, the server closes with `auth_expired`.
- Tokens never appear in URLs, query strings or logs.
- Application close codes include `auth_failed`, `auth_expired`, `superseded`, `schema_unsupported` and `rate_limited`.
- Replaced the earlier ticket-based proposal. Reason: a first-message token avoids URL leakage without adding a ticket service.

### Behaviour
- Bounded queues and backpressure; slow consumers receive `stream.warning`.
- `transcript.final` includes the persisted message ID; the client de-duplicates by ID.
- `transcript.partial` is never persisted and is held in memory only by the UI.
- Persistence of finals is by the server; JS does not need to be alive. JS catches up on foreground using sync pull.
- One active stream per user **[Approved A11]**: a newer authenticated stream triggers `superseded` on the older one or is rejected (policy to be confirmed).

## 13. Database entities and rules
Entities: `users`, `user_settings`, `day_sessions`, `conversations`, `transcript_messages`, `transcript_bookmarks`, `capture_gaps`, `session_events`, `stream_checkpoints`, `sync_tombstones`, `processed_operations`, `consent_records`.
- UUID primary keys; clients may supply IDs.
- UTC `TIMESTAMPTZ`; `local_date` and `timezone` on day sessions and conversations.
- `original_text` is immutable (enforced by a trigger); `edited_text` is nullable; translation is separate.
- Composite ownership constraints so a child cannot reference another user's parent.
- Unique de-duplication key `(user_id, source_stream_id, source_event_key)`.
- Stream checkpoints contain metadata only, never audio.
- Ownership enforced in every repository operation. Row-level security is under consideration, not decided.
- Versioned migrations with rollback tests.

## 14. Initial PostgreSQL schema
Illustrative DDL for review; Alembic or equivalent migrations are authored in M1. `pg_trgm` and any search-specific indexes are intentionally omitted until the search spike (T1.1) decides. The column-list form `ON DELETE SET NULL (column)` requires PostgreSQL 15 or later; the minimum PostgreSQL version is **[Unverified]** and is fixed in T0.1 against the managed-database offering.

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 auth_subject TEXT NOT NULL UNIQUE,            -- Firebase uid
 email TEXT,
 display_name TEXT,
 timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata', -- profile fallback only; sessions store their own
 sync_counter BIGINT NOT NULL DEFAULT 0,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_settings (
 user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 preferred_language TEXT,                       -- NULL until chosen from verified catalog
 ui_locale TEXT,
 font_scale NUMERIC(3,2) NOT NULL DEFAULT 1.00,
 high_contrast BOOLEAN NOT NULL DEFAULT false,
 auto_segmentation_enabled BOOLEAN NOT NULL DEFAULT true,
 silence_threshold_ms INTEGER NOT NULL DEFAULT 2000,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE consent_records (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 consent_type TEXT NOT NULL,
 notice_version TEXT NOT NULL,
 locale TEXT,
 accepted_at TIMESTAMPTZ NOT NULL
);

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
);
CREATE INDEX idx_day_user_date ON day_sessions(user_id, local_date DESC);
CREATE INDEX idx_day_sync ON day_sessions(user_id, sync_rev);

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
 FOREIGN KEY (day_session_id, user_id) REFERENCES day_sessions(id, user_id) ON DELETE CASCADE,
 CHECK ((source = 'specific' AND day_session_id IS NULL)
     OR (source <> 'specific' AND day_session_id IS NOT NULL)),
 UNIQUE (day_session_id, segment_order) DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX idx_conv_user_date ON conversations(user_id, local_date DESC);
CREATE INDEX idx_conv_sync ON conversations(user_id, sync_rev);

CREATE TABLE transcript_messages (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 conversation_id UUID NOT NULL,
 source_stream_id UUID NOT NULL,
 source_event_key TEXT NOT NULL,
 speaker_label TEXT,
 original_text TEXT NOT NULL,                  -- immutable (trigger)
 edited_text TEXT,                             -- NULL = not edited; non-empty when set
 edited_at TIMESTAMPTZ,
 display_text TEXT GENERATED ALWAYS AS (COALESCE(edited_text, original_text)) STORED,
 search_text TEXT NOT NULL,                    -- normalised display text, maintained by service layer
 search_norm_version SMALLINT NOT NULL,
 original_language TEXT,                       -- app code
 provider_locale TEXT,                         -- provider-returned
 translated_text TEXT,
 started_at TIMESTAMPTZ,
 ended_at TIMESTAMPTZ,
 timestamp_source TEXT NOT NULL CHECK (timestamp_source IN ('provider_offsets','chunk_bracketed','server_received')),
 confidence NUMERIC(5,4),
 sequence_number BIGINT,
 sync_rev BIGINT NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (id, user_id),
 UNIQUE (user_id, source_stream_id, source_event_key),
 FOREIGN KEY (conversation_id, user_id) REFERENCES conversations(id, user_id) ON DELETE CASCADE,
 CHECK (edited_text IS NULL OR length(edited_text) > 0)
);
CREATE INDEX idx_msg_conv_time ON transcript_messages(conversation_id, started_at, source_stream_id, sequence_number);
CREATE INDEX idx_msg_sync ON transcript_messages(user_id, sync_rev);
-- Trigger (authored in migrations): reject UPDATE of original_text, source_stream_id, source_event_key.

CREATE TABLE transcript_bookmarks (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 transcript_message_id UUID NOT NULL,
 note TEXT,
 sync_rev BIGINT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (user_id, transcript_message_id),
 FOREIGN KEY (transcript_message_id, user_id) REFERENCES transcript_messages(id, user_id) ON DELETE CASCADE
);

CREATE TABLE capture_gaps (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 day_session_id UUID,
 conversation_id UUID,
 client_gap_id UUID,                           -- idempotency for client-reported gaps
 reason TEXT NOT NULL CHECK (reason IN (
   'os_interruption','network_loss','provider_error','provider_throttle',
   'permission_revoked','route_change','process_terminated','auth_expired',
   'rotation_uncertain','unknown')),
 reported_by TEXT NOT NULL CHECK (reported_by IN ('client','server')),
 started_at TIMESTAMPTZ NOT NULL,
 ended_at TIMESTAMPTZ,                         -- NULL while open
 end_estimated BOOLEAN NOT NULL DEFAULT false, -- true when closed by inference (e.g. process death)
 sync_rev BIGINT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (user_id, client_gap_id),
 FOREIGN KEY (day_session_id, user_id) REFERENCES day_sessions(id, user_id) ON DELETE CASCADE,
 FOREIGN KEY (conversation_id, user_id) REFERENCES conversations(id, user_id) ON DELETE CASCADE
);
CREATE INDEX idx_gap_day ON capture_gaps(user_id, started_at);

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
 FOREIGN KEY (day_session_id, user_id) REFERENCES day_sessions(id, user_id) ON DELETE CASCADE,
 FOREIGN KEY (conversation_id, user_id) REFERENCES conversations(id, user_id) ON DELETE CASCADE
);

CREATE TABLE stream_checkpoints (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 conversation_id UUID,                        -- current routing target
 client_stream_id UUID NOT NULL,
 last_accepted_sequence BIGINT NOT NULL DEFAULT 0,
 anchor_utc TIMESTAMPTZ,
 clock_skew_ms INTEGER,
 provider_id TEXT,
 provider_locale TEXT,
 provider_session_count INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (user_id, client_stream_id),
 FOREIGN KEY (conversation_id, user_id) REFERENCES conversations(id, user_id) ON DELETE SET NULL (conversation_id)
);

CREATE TABLE sync_tombstones (
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 entity_type TEXT NOT NULL,
 entity_id UUID NOT NULL,
 merged_into_id UUID,
 sync_rev BIGINT NOT NULL,
 deleted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY (user_id, entity_type, entity_id)
);
CREATE INDEX idx_tomb_sync ON sync_tombstones(user_id, sync_rev);

CREATE TABLE processed_operations (
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 op_id UUID NOT NULL,
 response_status SMALLINT NOT NULL,
 processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY (user_id, op_id)
);
```

Schema changes from the previous version and why:
- `transcript_messages.text` replaced by `original_text` and `edited_text`; `is_final` removed (only finals are stored); `event_key` replaced by `source_stream_id` plus `source_event_key` with a user-scoped unique key.
- `user_settings.enabled_languages` removed and `preferred_language` default `'ta'` removed (catalog-driven).
- `day_sessions.mode` values reduced to `full_day_hybrid`.
- `conversations` gained `local_date`, `timezone`, containment CHECK and a deferrable unique `segment_order`.
- Added `capture_gaps`, `sync_tombstones`, `processed_operations`, `consent_records`, sync columns and composite ownership keys.
- The `stream_checkpoints.conversation_id` is the current routing target and is updated by split, merge and New Conversation.

## 15. Search **[Approved A10]**
- `search_text` = Unicode NFC of displayed text, with ZWJ/ZWNJ handling, case folding, punctuation removal and whitespace collapse. Query text uses the same function. `search_norm_version` allows re-indexing.
- Normalisation is implemented once in the backend and again on the device; shared test vectors (all six scripts, including conjuncts, Malayalam chillus and joiner cases) must pass in both.
- Candidate strategies, chosen by the spike (T1.1): trigram index on `search_text`; Postgres full-text with the `simple` configuration; application-side tokenisation; or per-user bounded substring scan. Locale and collation affect how Postgres parsers treat Indic combining marks **[Unverified]**; the spike tests this explicitly with a real corpus.
- Results are scoped by `user_id`, optional date range and cursor pagination.
- Field-level encryption of transcripts is an open decision because it prevents server-side substring search.

## 16. Recovery and error handling
- Permission denied: explain and offer settings route.
- OS interruption: stop/pause safely, persist confirmed text, open a capture gap and alert visually and by haptics. If the platform cannot resume automatically, ask the user to resume.
- Network loss: bounded retry with exponential backoff; replay within the window; gap if exceeded.
- Duplicate delivery: event IDs plus the user-scoped unique key.
- ASR failure: show warning, create a server-detected gap for unrecognised audio; never fabricate missing text.
- Process death: the server keeps confirmed transcripts. The engine recovers metadata only. A gap open at termination is closed on the next signal with `end_estimated = true`.
- Provider throttling: back off and show a degraded state.
- Sync failures follow §7.

## 17. Security and observability
- TLS everywhere. Firebase ID token verification server-side with the Firebase Admin credentials held in a secrets manager.
- No tokens in URLs or logs. Never log audio, tokens or full transcript text.
- Least-privilege IAM, encryption at rest, user-scoped queries plus composite foreign keys.
- Rate limits per user on REST and WebSocket.
- Local store protections per §6.
- Monitor safe metadata: stream success, reconnects, rotations, gap counts by reason, latency, provider error codes, interruption counts, sync failures.
- Provider audio retention and training policy are verified before real audio is sent (T0.2).

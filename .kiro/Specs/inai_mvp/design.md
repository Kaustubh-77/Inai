# Inai MVP — Design

## 1. Architecture
React Native + TypeScript shared app; Kotlin Android capture adapter; Swift iOS capture adapter; FastAPI backend; authenticated TLS WebSocket; provider-neutral ASR adapter; PostgreSQL persistence.

## 2. Mobile components
- Home: Start My Day, Start Conversation, today's sessions.
- Recording: large captions, language, elapsed time, recording state, pause/resume/stop.
- Day history: group by stored local date/timezone.
- Conversation detail: timestamped chat-like transcript, edit and bookmark.
- Settings: verified languages, caption size, contrast and segmentation preferences.
- RecordingController: shared session state machine.
- NativeRecordingBridge: typed interface to platform capture.
- API and realtime clients: authenticated REST/WebSocket.

## 3. Native capture
### Android
Kotlin capture module and user-initiated foreground service where required. Handle permission, persistent notification, route changes, interruptions, process/lifecycle recovery and service failure.

### iOS
Swift module using AVAudioSession and AVAudioEngine or justified equivalent. Handle permission, session activation, interruptions, route changes and permitted background behaviour. Do not imply unrestricted background recording.

### Shared interface
Expose permission state, platform capabilities, start/pause/resume/stop, audio frame events and state/interruption events.

## 4. State machine
Suggested states: `idle`, `requesting_permission`, `ready`, `recording_specific`, `recording_day`, `paused`, `stopping`, `saved`, `interrupted`, `error`. An OS interruption must not be misrepresented as a user pause. Preserve last confirmed transcript sequence.

## 5. Audio pipeline
Native capture → bounded PCM frames → VAD → chunker → authenticated WebSocket → backend ASR adapter → partial/final events → final transcript persistence. Discard audio buffers after processing. Do not hard-code audio format until provider requirements are verified.

## 6. Segmentation
- DaySession contains multiple Conversation records.
- VAD speech-start opens a candidate segment.
- Sustained silence proposes a boundary with a grace window.
- Configurable initial silence threshold for testing: 1.5–2.5 seconds.
- Manual New Conversation closes the current segment and starts the next on speech.
- Split/merge preserve timestamps and order.
- Empty segments are discarded.

## 7. REST API
| Method/path | Purpose |
|---|---|
| `POST /v1/day-sessions` | Create day |
| `GET /v1/day-sessions?from=&to=` | List days |
| `GET /v1/day-sessions/{id}` | Get day and conversations |
| `POST /v1/day-sessions/{id}/pause` | Pause |
| `POST /v1/day-sessions/{id}/resume` | Resume |
| `POST /v1/day-sessions/{id}/end` | End |
| `POST /v1/conversations` | Create conversation/segment |
| `GET /v1/conversations/{id}` | Fetch transcript |
| `PATCH /v1/conversations/{id}` | Rename/update |
| `POST /v1/conversations/{id}/split` | Split |
| `POST /v1/conversations/{id}/merge` | Merge |
| `PATCH /v1/transcript-messages/{id}` | Edit transcript |
| `GET /v1/search?q=&from=&to=` | Search |
| `GET /v1/conversations/{id}/export` | Export |
| `DELETE /v1/conversations/{id}` | Delete conversation |
| `DELETE /v1/day-sessions/{id}` | Delete day |

Derive user identity from verified authentication. Never trust request-body `user_id`.

## 8. WebSocket events
Endpoint example: `/v1/stream`. Events: `stream.start`, `audio.chunk`, `transcript.partial`, `transcript.final`, `segment.suggested`, `stream.warning`, `stream.end`, `stream.closed`. Include schema version, event ID, sequence and timestamps. Use acknowledgements, idempotency, backpressure and bounded queues.

## 9. Database entities and rules
Entities: `users`, `user_settings`, `day_sessions`, `conversations`, `transcript_messages`, `transcript_bookmarks`, `session_events`, `stream_checkpoints`.
- UUID primary keys.
- UTC `TIMESTAMPTZ`.
- Store `local_date` and `timezone` on day sessions.
- Keep original transcript and optional translation separate.
- Unique event key per conversation prevents duplicate final messages.
- Stream checkpoints contain metadata only, never audio.
- Enforce user ownership in every repository operation.

## 10. Initial PostgreSQL schema
```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 auth_subject TEXT NOT NULL UNIQUE,
 email TEXT,
 display_name TEXT,
 timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_settings (
 user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 preferred_language TEXT NOT NULL DEFAULT 'ta',
 enabled_languages TEXT[] NOT NULL DEFAULT ARRAY['ta','kn','ml','te','hi','en'],
 font_scale NUMERIC(3,2) NOT NULL DEFAULT 1.00,
 high_contrast BOOLEAN NOT NULL DEFAULT false,
 auto_segmentation_enabled BOOLEAN NOT NULL DEFAULT true,
 silence_threshold_ms INTEGER NOT NULL DEFAULT 2000,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE day_sessions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 local_date DATE NOT NULL,
 timezone TEXT NOT NULL,
 mode TEXT NOT NULL CHECK (mode IN ('full_day','mixed')),
 status TEXT NOT NULL CHECK (status IN ('active','paused','completed','interrupted')),
 started_at TIMESTAMPTZ NOT NULL,
 ended_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_day_user_date ON day_sessions(user_id,local_date DESC);

CREATE TABLE conversations (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 day_session_id UUID REFERENCES day_sessions(id) ON DELETE CASCADE,
 title TEXT,
 source TEXT NOT NULL CHECK (source IN ('specific','auto_segment','manual_segment')),
 status TEXT NOT NULL CHECK (status IN ('active','paused','completed','interrupted')),
 language_hint TEXT,
 started_at TIMESTAMPTZ NOT NULL,
 ended_at TIMESTAMPTZ,
 segment_order INTEGER,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_conv_day_order ON conversations(day_session_id,segment_order);

CREATE TABLE transcript_messages (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 event_key TEXT NOT NULL,
 speaker_label TEXT,
 text TEXT NOT NULL,
 original_language TEXT,
 translated_text TEXT,
 started_at TIMESTAMPTZ,
 ended_at TIMESTAMPTZ,
 is_final BOOLEAN NOT NULL DEFAULT true,
 confidence NUMERIC(5,4),
 sequence_number BIGINT,
 edited_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(conversation_id,event_key)
);
CREATE INDEX idx_msg_conv_time ON transcript_messages(conversation_id,started_at);

CREATE TABLE transcript_bookmarks (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 transcript_message_id UUID NOT NULL REFERENCES transcript_messages(id) ON DELETE CASCADE,
 note TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(user_id,transcript_message_id)
);

CREATE TABLE session_events (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 day_session_id UUID REFERENCES day_sessions(id) ON DELETE CASCADE,
 conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
 event_type TEXT NOT NULL,
 occurred_at TIMESTAMPTZ NOT NULL,
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE stream_checkpoints (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
 client_stream_id TEXT NOT NULL,
 last_accepted_sequence BIGINT NOT NULL DEFAULT 0,
 status TEXT NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(user_id,client_stream_id)
);
```

## 11. Recovery and error handling
- Permission denied: explain and offer settings route.
- OS interruption: stop/pause safely, persist confirmed text and mark interrupted when appropriate.
- Network loss: bounded retry with exponential backoff and sequence acknowledgement.
- Duplicate delivery: event IDs and database uniqueness.
- ASR failure: show warning; never fabricate missing text.
- Process death: recover metadata and confirmed transcript checkpoint only.
- Provider throttling: back off and show degraded state.

## 12. Security and observability
TLS, server-side secrets, least-privilege IAM, encryption at rest, user-scoped access. Do not log raw audio, tokens or full transcript text. Monitor safe metadata: stream success, reconnects, latency, provider error codes and interruption counts.

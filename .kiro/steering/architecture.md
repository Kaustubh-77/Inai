# Inai — Architecture Steering

Items marked **[Approved Ax]** are decisions from the 2026-11 specification amendment, approved by the owner on 2026-11-25 (A1–A14). Items marked **[Unverified]** must be confirmed in the validation gate (`docs/architecture/platform-provider-validation.md`) before being relied on.

## System
- Shared mobile UI/domain: React Native + TypeScript. Owns screens, session presentation, transcript events, local-store access, sync and accessible presentation.
- Native audio engine: Kotlin on Android and Swift on iOS. Each platform engine owns microphone permission, capture, VAD, chunking and the streaming transport to the backend. **Raw audio never crosses into JavaScript.**
- Android capture: native Kotlin module and user-initiated foreground service, following current Android rules.
- iOS capture: native Swift module using AVAudioSession and AVAudioEngine or justified equivalent.
- Identity: Firebase Authentication for the MVP. The backend verifies Firebase ID tokens server-side.
- Device persistence: SQLite local store for offline reading and editing of previously synchronised transcripts, with a pending-operation queue.
- Backend: Python + FastAPI.
- Realtime: authenticated TLS WebSocket. Credentials are sent in the first message, never in the URL.
- Speech recognition: provider-neutral ASR adapter. Sarvam AI is the first candidate to evaluate. **No provider is selected or confirmed.**
- Persistence: PostgreSQL (server source of truth).
- Operations: cloud secrets, least-privilege access, monitoring and cost controls. Cloud vendor and region are undecided.

## Separation of responsibilities
- **Native engine** owns: permissions, capture, OS audio sessions, interruptions, platform lifecycle, VAD, chunking, bounded in-memory replay buffer, WebSocket transport, reconnect, and the authoritative capture/stream state.
- **Shared app (JS)** owns: screens, presentation state, REST client, local SQLite store, sync engine, and a projection of native state. JS may be suspended or absent while the native engine keeps running; the design must not depend on JS being alive during capture.
- **Backend** owns: authentication verification, ASR provider sessions, finals persistence, timestamp mapping, conversation routing, sync revisions.
- Do not force Android/iOS behaviour into one generic native implementation. Share the contract, not the code.

## Native engine interface
Typed operations equivalent to:
- requestPermission(), getPermissionState(), getPlatformCapabilities()
- configureEngine(config), getEngineStatus() (lets JS re-attach after restart)
- startCapture(params), pauseCapture(), resumeCapture(), stopCapture()
- requestNewConversation()
- updateAuthToken(token) (fallback path; see Identity)
- subscribeToStateChanges() — capture state, interruptions, capabilities
- subscribeToStreamEvents() — transcript.partial/final, segment.opened, stream.warning, capture-gap open/close, connectivity status

Removed: `subscribeToAudioFrames()`. Reason: approved decision that native owns VAD, chunking and transport, so no audio frames are delivered to JS.

Return platform capability and interruption details. Never advertise a capability the current OS/build cannot provide. The engine sends the app language code only; provider locale mapping is server-side.

## Audio pipeline
1. Native capture produces bounded PCM frames in memory.
2. Native VAD detects speech activity and suggests boundaries.
3. Native chunker creates bounded chunks using verified provider requirements.
4. Native transport streams chunks over the TLS WebSocket with sequence numbers and capture offsets.
5. Backend forwards audio to the ASR adapter.
6. Partial hypotheses are provisional and never persisted. Final events are persisted incrementally by the server.
7. Audio buffers are discarded. No raw audio is persisted anywhere, including the replay buffer, which is memory only.

Do not assume a sample rate, encoding, channel count, chunk size or ASR locale until verified against current provider documentation.

**[Approved A7]** Full-Day mode transmits VAD-gated audio only (speech plus configurable pre-roll/post-roll) to bound cost and battery. Specific Conversation streams continuously. VAD false negatives must be evaluated with target users before gating is enabled.

## Streaming lifecycle
- **Auth:** first message on the socket is `stream.auth` carrying a Firebase ID token. Connections that do not authenticate within a short timeout are closed. Tokens are never placed in URLs or logs. Re-auth happens in-band (`stream.reauth`) before expiry **[Approved A1]**.
- **Reconnect:** the client resumes by `client_stream_id`; the server returns the last accepted sequence. Native replays only unacknowledged chunks that are still inside a bounded **in-memory** replay window. Audio older than the window is lost and recorded as a capture gap. Window size is set by measurement **[Approved A8]**.
- **One active stream per user [Approved A11].** If a second stream is requested while one is active, the server rejects the new stream with the close code `stream_already_active` and a clear, user-readable message that another recording is already active. The existing stream is never terminated, superseded or otherwise affected. A reconnect that reuses the existing `client_stream_id` is a resume of that stream, not a second stream (see Resume, pause and expiry).
- **Resume, pause and expiry [Approved A11 clarification]:**
  - Every reconnect authenticates again with a Firebase ID token in the first message. The server resolves `client_stream_id` only within the authenticated user's own checkpoints and rejects a resume for a checkpoint the user does not own without revealing whether it exists. `client_stream_id` is an identifier, never a credential.
  - A valid resume continues the existing checkpoint and sequence numbering. It does not create a second provider session (a new one is created only if the previous one has already ended) and does not duplicate transcript messages.
  - An explicit user pause stays resumable and is not subject to the unexpected-disconnection timer. The user can explicitly resume or stop it.
  - An unexpected disconnection keeps the stream's active-stream slot for a finite, configurable reconnect grace window. Its initial value is an implementation/configuration decision that requires reconnect testing; no number is fixed here.
  - If the window expires, the stream is marked expired and interrupted, its slot is released, its provider session is cleaned up and the user is told. Previously persisted transcript data is kept. A late reconnect receives `stream_expired` and must start a new stream; an expired stream is never silently resumed.
- **Paused-stream recovery, races and restart [Approved A11 final clarification]:**
  - A paused stream holds the active-stream slot indefinitely unless explicitly ended; no pause timeout exists. The authenticated account owner can end it from another session or device through a server-side operation (`POST /v1/streams/{client_stream_id}/end`). Ownership is verified server-side, other users cannot end it, persisted transcripts are preserved, and the checkpoint becomes `ended`, releasing the slot. Only `paused` streams can be ended this way; a live stream is never terminated remotely.
  - Every checkpoint status change is an atomic compare-and-set in the database, so a valid resume and an expiry that run concurrently resolve to exactly one winner. A resume that wins can never be expired afterwards; an expiry that wins makes the late resume receive `stream_expired`.
  - A new stream after expiry has its own `client_stream_id`, checkpoint, provider session and sequence numbering. The expired checkpoint, the interruption history and the capture gap are preserved, and the missing audio is never presented as recovered.
  - A new stream may start automatically after expiry only while native capture is still running under the user's original explicit recording action, and the interruption and the new stream are visible to the user. Capture is never restarted after the user explicitly stopped it, or after the stream was ended remotely.
- **Provider session rotation:** the server owns provider sessions, separate from the device socket. Provider stream duration limits and idle timeouts are unverified; the adapter exposes them as capabilities. See design.md §8.

## Session model
- A DaySession (mode `full_day_hybrid`) contains zero or more Conversations.
- A specific conversation is standalone (no DaySession) but carries its own `local_date` and `timezone` so day-wise history works without a day container.
- A Conversation contains ordered TranscriptMessages.
- SessionEvents record pause, resume, interruption, boundary and end events.
- CaptureGaps record intervals where audio was not captured or not processed because of OS, network, permission or provider causes (not user pauses).
- StreamCheckpoints store IDs, accepted sequence numbers and timing metadata only, never audio.

## Segmentation
Native VAD opens a candidate segment on speech start. Sustained silence proposes a boundary with a grace window. In Full-Day mode with auto-segmentation enabled the boundary is applied automatically; otherwise it is recorded but not applied. The next conversation row is created lazily on the first accepted speech content, so empty conversations never exist. The user can manually create a new conversation, split, merge and rename. Preserve message timestamps when correcting segments.

## Timestamps
Native stamps each chunk with a monotonic `capture_offset_ms` relative to a stream anchor (device UTC + monotonic reading). The server maps provider results back to capture offsets and computes UTC timestamps, correcting for client clock skew. Each message records its `timestamp_source` so approximate timing is never presented as exact. Details in design.md §9.

## Capture gaps
Any interval of lost audio coverage is stored as a CaptureGap and shown inline in the transcript timeline. User pauses are not gaps. Never fabricate text for a gap, and never imply capture continued. Details in design.md §10.

## Identity and authorization
- Firebase Authentication for the MVP; sign-in methods are an open decision.
- Backend verifies the ID token signature, issuer, audience, expiry and subject. The verified `sub` maps to `users.auth_subject`; the user row is provisioned on first verified request.
- Derive user identity only from the verified principal. Never trust a client-supplied user_id.
- Native engine obtains tokens via the platform Firebase SDK session where possible, so background streams can refresh without JS **[Unverified]**. Fallback: JS pushes tokens while foregrounded and a stream that outlives its token ends as an `auth_expired` gap.
- Account deletion removes server data and the Firebase user, and wipes the local store.

## Local store and sync
- SQLite on device holds previously synchronised transcripts for offline reading, local search and editing, plus a pending-operation queue. The server is the source of truth; the device is a cache plus queued edits.
- Offline-capable operations: edit/revert message text, add/remove bookmark, rename conversation **[Approved A3]**. Split, merge, delete, export and all recording require connectivity.
- Sync is pull by per-user revision cursor plus idempotent push of queued operations. Text and title edits use compare-and-set against the last known server value. Conflicts are surfaced to the user and never silently overwritten **[Approved A4]**.
- Local store is encrypted at rest with a key in Keychain/Keystore **[Approved A2]**, excluded from device backups, and wiped on sign-out and account deletion **[Approved A12]**.
- Never store audio in SQLite.
- Details in design.md §6–7 and §12.

## Languages
Supported languages come from a server-side verified-language catalog that maps app codes (`ta`, `te`, `kn`, `ml`, `hi`, `en`) to provider locales and records verification status and evidence. The app lists only verified entries. No default language is assumed. Details in design.md §5.

## REST API proposal
- `GET /v1/me`, `PUT /v1/me/settings`, `DELETE /v1/me`, `POST /v1/consents`
- `GET /v1/languages`
- POST/GET `/v1/day-sessions`
- GET/DELETE `/v1/day-sessions/{id}`
- POST `/v1/day-sessions/{id}/pause|resume|end`
- POST `/v1/conversations`
- GET/PATCH/DELETE `/v1/conversations/{id}`
- POST `/v1/conversations/{id}/split|merge`
- PATCH `/v1/transcript-messages/{id}`
- PUT/DELETE `/v1/transcript-messages/{id}/bookmark`
- GET `/v1/search?q=&from=&to=`
- GET `/v1/conversations/{id}/export`
- GET `/v1/sync/changes?cursor=`
- GET `/v1/streams/active`, POST `/v1/streams/{client_stream_id}/end` (owner-only; ends a paused stream)

All routes require a verified Firebase ID token. Mutating routes accept an `Idempotency-Key`. Clients may supply UUIDs for creates.

## WebSocket events
Client to server: `stream.auth`, `stream.reauth`, `stream.start`, `audio.chunk`, `segment.suggested`, `segment.new`, `stream.pause`, `stream.resume`, `capture.gap`, `stream.end`.
Server to client: `stream.auth.ok`, `audio.ack`, `transcript.partial`, `transcript.final`, `segment.opened`, `stream.warning`, `stream.closed`.
Stream rejection, expiry and remote end are reported with close codes `stream_already_active`, `stream_expired`, `stream_not_found` and `stream_ended`.
Include schema version, event IDs, sequence numbers and timestamps. Use acknowledgements, idempotency, bounded buffers, backpressure and reconnect.

## Persistence
PostgreSQL entities: users, user_settings, day_sessions, conversations, transcript_messages, transcript_bookmarks, session_events, capture_gaps, stream_checkpoints, sync_tombstones, processed_operations, consent_records. Use UUIDs, UTC `TIMESTAMPTZ`, and store local date/timezone on DaySession and Conversation.

Transcript messages keep `original_text` (immutable) and `edited_text` (nullable) separately; the displayed text is `edited_text` when present, else `original_text`. Translation remains a separate optional field and never overwrites either.

Message de-duplication identity is user-scoped and immutable (`user_id, source_stream_id, source_event_key`), so split and merge never require event-key remapping.

## Search
Search runs against a normalised `search_text` (Unicode NFC, joiner handling, case folding). Postgres full-text stemming does not cover Tamil, Telugu, Kannada or Malayalam, and default tokenisers may mishandle Indic combining marks, so the search strategy is chosen by a validation spike with per-script test corpora. The same normalisation (shared test vectors) is used by the server and the local store.

## Security/observability
TLS, encryption at rest, server-side secrets (including Firebase Admin and ASR credentials), least-privilege IAM, user-scoped access. Do not log audio, tokens or full transcript text by default. Monitor safe metadata such as latency, disconnects, rotations, gap counts and provider errors.

## Verification gates
Verify current Android foreground-service rules, iOS background audio rules, React Native native-module support, native Firebase token access from background, ASR streaming support for all six languages and the intended region, provider timestamps, stream duration limits, audio retention/training policy, quotas/pricing, SQLite library encryption and search-tokenizer support, and App Store/Play policies. Record evidence in `docs/architecture/platform-provider-validation.md`. Real user audio must not be sent to any provider until its retention and training policy has been verified.

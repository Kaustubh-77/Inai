# Inai — Architecture Steering

## System
- Shared mobile UI/domain: React Native + TypeScript.
- Android capture: native Kotlin module and user-initiated foreground service, following current Android rules.
- iOS capture: native Swift module using AVAudioSession and AVAudioEngine or justified equivalent.
- Backend: Python + FastAPI.
- Realtime: authenticated TLS WebSocket.
- Speech recognition: provider-neutral ASR adapter.
- Persistence: PostgreSQL.
- Operations: cloud secrets, least-privilege access, monitoring and cost controls.

## Separation of responsibilities
The shared app owns screens, domain/session state, API contracts and accessible presentation. Native modules own microphone permissions, audio capture, OS audio sessions, interruptions and platform lifecycle. Do not force Android/iOS recording behaviour into one generic native implementation.

## Recording interface
Expose typed operations equivalent to:
- requestPermission()
- getPermissionState()
- getPlatformCapabilities()
- startCapture(config)
- pauseCapture()
- resumeCapture()
- stopCapture()
- subscribeToAudioFrames()
- subscribeToStateChanges()

Return platform capability and interruption details. Never advertise a capability the current OS/build cannot provide.

## Audio pipeline
1. Native capture emits bounded PCM frames.
2. VAD detects speech activity and suggests boundaries.
3. Chunker creates bounded chunks using verified provider requirements.
4. Client streams chunks over TLS WebSocket with sequence numbers.
5. Backend forwards chunks to ASR.
6. Partial hypotheses are provisional; final events are persisted incrementally.
7. Audio buffers are discarded. No raw audio is persisted.

Do not assume a sample rate, encoding, channel count, chunk size or ASR locale until verified against current provider documentation.

## Session model
- A DaySession contains zero or more Conversations.
- A Conversation contains ordered TranscriptMessages.
- A specific conversation may be attached to the day container for day-wise history.
- SessionEvents record pause, resume, interruption, boundary and end events.
- StreamCheckpoints store IDs and accepted sequence numbers only, never audio.

## Segmentation
VAD opens a candidate segment on speech start. Sustained silence proposes a boundary with a grace window. User can manually create a new conversation, split, merge and rename. Never create empty conversations. Preserve message timestamps when correcting segments.

## REST API proposal
- POST/GET `/v1/day-sessions`
- GET `/v1/day-sessions/{id}`
- POST `/v1/day-sessions/{id}/pause|resume|end`
- POST `/v1/conversations`
- GET/PATCH/DELETE `/v1/conversations/{id}`
- POST `/v1/conversations/{id}/split|merge`
- PATCH `/v1/transcript-messages/{id}`
- GET `/v1/search?q=&from=&to=`
- GET `/v1/conversations/{id}/export`

All routes require authentication. Derive user identity from the verified principal, never trust a client-supplied user_id.

## WebSocket events
`stream.start`, `audio.chunk`, `transcript.partial`, `transcript.final`, `segment.suggested`, `stream.warning`, `stream.end`, `stream.closed`. Include schema version, event IDs, sequence numbers and timestamps. Use acknowledgements, idempotency, bounded buffers, backpressure and reconnect.

## Persistence
PostgreSQL entities: users, user_settings, day_sessions, conversations, transcript_messages, transcript_bookmarks, session_events and stream_checkpoints. Use UUIDs, UTC `TIMESTAMPTZ`, and store local date/timezone on DaySession. Preserve original text separately from optional translation.

## Security/observability
TLS, encryption at rest, server-side secrets, least-privilege IAM, user-scoped access. Do not log audio, tokens or full transcript text by default. Monitor safe metadata such as latency, disconnects and provider errors.

## Verification gates
Verify current Android foreground-service rules, iOS background audio rules, React Native native-module support, ASR streaming support for all six languages and the intended region, provider quotas/pricing, and App Store/Play policies. Record evidence in `docs/architecture/platform-provider-validation.md`.

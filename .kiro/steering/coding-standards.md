# Inai — Coding Standards

Aligned with the specification amendments A1–A14 approved on 2026-11-25. Items marked **[Unverified]** depend on the validation gate (T0.2).

## General
- Use small, reviewable changes and typed interfaces.
- Do not silently change approved product decisions or API contracts.
- Never claim a feature or test is complete unless it was run and verified.
- Handle loading, empty, offline, permission-denied and error states.
- Do not hard-code a language, provider locale, audio format, sample rate, chunk size or provider limit. Read them from the verified language catalog or the provider adapter capabilities.
- Do not treat any ASR provider as selected. Sarvam AI is a candidate under evaluation only.

## React Native / TypeScript
- Enable strict TypeScript.
- Avoid `any`; type API payloads, native events, WebSocket messages and local-store rows.
- Keep domain logic out of presentational components.
- Keep native recording behind the typed native engine interface. Raw audio never crosses into JavaScript; JS receives state, stream and transcript events only.
- Treat the native engine as the authority for capture and stream state. The JS RecordingController is a projection and must not assume JS stays alive during capture.
- Display `edited_text` when present, otherwise `original_text`. Never overwrite `original_text`.
- Partial captions are held in memory only. Never persist them or announce them to screen readers.
- Local store (SQLite): versioned forward-only migrations, encryption at rest, never store audio or tokens, and wipe on sign-out and account deletion.
- Sync: queue offline operations with idempotency keys, use compare-and-set for text and title edits, and surface conflicts to the user. Never discard queued operations on 401.
- Use the shared search-normalisation function and its shared test vectors; do not implement a second variant.
- Use accessible labels, roles and logical focus order.
- Never embed cloud secrets or provider credentials in the app. Authentication uses the Firebase SDK; do not store or log ID tokens elsewhere.

## Kotlin / Android
- Follow current Android permission and foreground-service requirements, including the microphone service type and notification permission where required.
- The native engine owns capture, VAD, chunking, the replay buffer and the WebSocket transport.
- Start microphone capture only from a visible user-initiated state; do not attempt to start it from the background.
- Keep capture lifecycle explicit and use bounded buffers. The replay buffer is memory only.
- Handle permission revocation, audio focus, interruptions and route changes, and report capture gaps accurately.
- Never write captured audio to disk or pass it to JS under the current product policy.

## Swift / iOS
- Use explicit AVAudioSession lifecycle management.
- The native engine owns capture, VAD, chunking, the replay buffer and the WebSocket transport.
- Handle interruptions, route changes and session reactivation, and report capture gaps accurately.
- Do not assume background execution is unrestricted.
- Never persist raw audio or pass it to JS under the current product policy. The replay buffer is memory only.

## Python / FastAPI
- Use type hints and request/response schemas.
- Separate routes, domain services, repositories and provider adapters.
- Validate all input and derive user identity only from the verified Firebase ID token (signature, issuer, audience, expiry). Never trust a client-supplied user_id.
- WebSocket authentication is the first message (`stream.auth`) with in-band re-auth. Never accept tokens in URLs or query strings and never log them.
- Use idempotency keys on mutating requests and a consistent problem-details error model.
- Keep provider-specific behaviour behind the adapter. Provider limits and capabilities come from adapter capability flags, not assumptions.
- Use async-safe code in streaming paths and safe error responses.

## Database
- Use versioned migrations, UUIDs and `TIMESTAMPTZ`.
- Store local date and timezone explicitly on day sessions and conversations.
- Enforce user ownership with repository checks and composite keys, and test cross-user access.
- `original_text` is immutable (trigger-enforced). `edited_text` is nullable. Keep any translation as a separate field.
- Message de-duplication identity is `(user_id, source_stream_id, source_event_key)`, immutable and independent of the conversation.
- Assign `sync_rev` from the per-user counter inside the writing transaction. Deletes write content-free tombstones.
- Maintain `search_text` with the shared normalisation and `search_norm_version`.

## Testing and logging
- Unit-test state transitions and segmentation.
- Test APIs, migrations, WebSocket ordering/retries/duplicates, auth failure and token expiry.
- Test local-store migrations, offline edits, conflict scenarios, cursor expiry and sign-out with pending operations.
- Test split/merge routing, timestamp mapping, capture gaps and provider session rotation with the fake provider.
- Test search normalisation with the shared per-script vectors on server and device.
- Test microphone lifecycle on physical Android and iOS devices.
- Never log raw audio, credentials, access tokens (including in URLs) or full transcript text by default.
- Do not fabricate device, language or accuracy results.

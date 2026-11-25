# Inai MVP — Implementation Tasks

## Working rules
Work in small increments. Read steering and Spec files before each task. Add tests and documentation with each vertical slice. Do not mark work complete unless tests/builds were run. Do not deploy paid resources or publish builds without explicit approval. Do not configure paid services, create cloud resources or generate credentials without explicit approval. Do not send real user audio to any ASR provider until its retention and training policy has been verified (T0.2) and recorded. Items marked **[Approved Ax]** were approved on 2026-11-25.

## Ordering rationale **[Approved A14: milestone reorder and task renumbering]**
Backend and protocol work that can be verified without devices comes first (M1–M2). Mobile shell, domain and local store follow (M3). Native engines need the VAD design and the platform evidence (M4). Real ASR is integrated only after provider validation and the legal review kickoff (M5). Full-day mode builds on the specific-conversation path (M6). This replaces the previous order, which placed VAD after live captions although VAD precedes the chunker in the pipeline.

## Milestone 0 — Foundation and decisions
### T0.1 Repository/toolchain inspection
Inspect repository, Kiro conventions, Node/package manager, React Native build approach, Python, PostgreSQL (confirm minimum version for the schema) and native build prerequisites. Record what the sandbox can and cannot build (no Xcode on Linux; Android SDK and PostgreSQL absent at last inspection). Document setup.
**Done when:** reproducible local setup guide exists; architecture is reviewed before implementation.

### T0.2 Platform and provider validation
Verify and record source URL, date, limitations, pricing and quotas for:
- Android microphone/foreground-service rules (including Android 15/16 and Play declarations), iOS microphone/AVAudioSession/background rules, and React Native native-module support.
- Native Firebase SDK token access from a background engine, and the fallback behaviour if unavailable.
- Streaming ASR for `ta`, `kn`, `ml`, `te`, `hi`, `en` in the intended region, starting with Sarvam AI as the first candidate and comparing at least one alternative. Record: streaming vs batch, partial results, audio format, segment offsets, session duration and idle limits, region, pricing, quotas, **audio retention/logging/training policy**.
- SQLite library options: encryption, FTS tokenizers, New Architecture support, backup exclusion.
Do not select a final provider in this task; selection is a separate owner decision.
**Done when:** `docs/architecture/platform-provider-validation.md` capability matrix exists, the language catalog statuses are justified by evidence, and unsupported assumptions are not hard-coded.

### T0.3 Steering and structure verification
Steering files already exist. Verify they match the approved architecture and amended specs, and create the missing app/backend/infra/docs directory structure.
**Done when:** structure is committed and steering/spec files are consistent (no unresolved contradictions).

### T0.4 Quality baseline
Configure formatting, lint, type checks and test commands for TypeScript, Python and (where buildable) Kotlin/Swift.
**Done when:** baseline checks run locally and in CI; iOS CI runner availability is recorded.

### T0.5 Legal/privacy review kickoff
Begin jurisdiction-specific review of consent, bystander recording and data-protection obligations, and draft the privacy notice, recording-responsibility notice and provider disclosure. Plan deaf and hard-of-hearing participant recruitment and informed consent.
**Done when:** review engaged and open questions logged; findings must be available before T5.1.

## Milestone 1 — Backend core (verifiable without devices)
### T1.1 Indic-script search spike
Build per-script test corpora (Latin, Devanagari, Tamil, Telugu, Kannada, Malayalam) and shared normalisation test vectors. Evaluate candidate strategies on PostgreSQL (trigram, `simple` full-text, application-side tokenisation, bounded substring scan) and, for the device, SQLite options. Record the decision.
**Done when:** a documented, tested strategy exists for server and device with identical normalisation results.

### T1.2 Migrations/models
Implement users, settings, day_sessions, conversations, transcript_messages (`original_text`/`edited_text`, immutability trigger), bookmarks, capture_gaps, session_events, stream_checkpoints, sync_tombstones, processed_operations, consent_records, with composite ownership keys.
**Done when:** migrations and rollback tests pass; trigger and constraint tests pass.

### T1.3 Firebase authentication and ownership
Verify Firebase ID tokens server-side (signature, issuer, audience, expiry), provision users, and enforce ownership on all repositories and routes. Use local test doubles or the Firebase emulator; do not create cloud projects or credentials without approval.
**Done when:** invalid/expired/wrong-audience/missing-token and cross-user tests fail safely.

### T1.4 Language catalog
Implement the schema-validated language catalog and `GET /v1/languages`, with no verified entries unless T0.2 evidence exists.
**Done when:** unverified languages are never returned; empty catalog behaviour is tested.

### T1.5 REST APIs
Implement account, settings, consent, day/conversation, transcript edit/revert (compare-and-set), bookmark, export, deletion (with tombstones), account deletion, idempotency keys and the error model.
**Done when:** API tests cover success, validation, idempotency, ownership failures, and edit never altering `original_text`.

### T1.6 Split and merge
Implement split and merge including routing updates for stream checkpoints, ordering, gaps, bookmarks and tombstones.
**Done when:** timestamps, ordering, bookmarks and de-duplication are preserved; retried finals after split/merge do not duplicate. **[Approved A5]**

### T1.7 Sync API
Implement the per-user revision counter, `GET /v1/sync/changes`, tombstone retention and `cursor_expired`.
**Done when:** concurrent-write tests show no skipped revisions; full resync path tested. **[Approved A4]**

### T1.8 Search implementation
Implement search per T1.1 decision.
**Done when:** per-script corpus tests and user-scoping tests pass.

## Milestone 2 — Streaming protocol with fake ASR
### T2.1 WebSocket protocol
Implement versioned events, first-message authentication, in-band re-auth, close codes, sequence numbers, acknowledgements, idempotency, bounded queues and backpressure; decide audio framing from T0.2 evidence. **[Approved A1]**
**Done when:** ordering, duplicate, reconnect, auth-failure, expiry and token-not-in-URL/log tests pass.

### T2.2 ASR adapter and fake provider
Implement the provider-neutral interface, capability flags and a fake provider. Real ASR is integrated only in T5.1.
**Done when:** partial, final, timeout, throttling and failure tests pass.

### T2.3 Timestamp mapping
Implement anchor, clock-skew handling, provider-to-capture offset mapping and `timestamp_source`.
**Done when:** tests cover pauses, VAD gating, reconnects, clock skew and providers with and without offsets.

### T2.4 Gaps and replay semantics (server side)
Implement `audio.ack`, resume by `client_stream_id` (ownership and expiry rules are specified in T2.6), `capture_gaps` creation (client-reported and server-detected) with the deterministic reconciliation rule in design.md §8 (one canonical row per gap, idempotent reports, closure on first accepted audio), and idempotent gap reporting.
**Done when:** gap and resume tests pass (reconciliation tests are listed under T2.6); no text is invented for gaps. **[Approved A8]**

### T2.5 Provider session rotation
Implement session lifecycle, idle close, planned rotation at silence, forced rotation with overlap de-duplication, using the fake provider with simulated limits.
**Done when:** simulated long sessions produce no lost or duplicated speech beyond documented limits.

### T2.6 One-active-stream policy
Implement rejection of a second stream with the `stream_already_active` close code and a user-readable error message, with an atomic check against the user's active stream. The existing stream must continue unaffected. Implement resume with the safeguards below, using a configurable reconnect grace window whose initial value is **not fixed** (set after reconnect testing). **[Approved A11 and clarification]**
- Resume: Firebase authentication on every reconnect, ownership verification of the checkpoint, `client_stream_id` treated as an identifier and not a credential, reuse of the existing checkpoint, sequence numbering and live provider session.
- Intentional pause stays resumable and is exempt from the grace timer; the user can resume or stop it.
- Paused streams hold the slot indefinitely (no pause timeout). Implement the owner-only `GET /v1/streams/active` and `POST /v1/streams/{client_stream_id}/end` operations: ownership verified server-side, only `paused` endable, atomic `ended` transition that releases the slot, closes any provider session, completes the associated sessions and preserves persisted transcripts, with the confirmation and outcome messages defined in the design.
- All checkpoint transitions are database-level compare-and-set operations so resume and expiry can never both win.
- After expiry a new stream has its own `client_stream_id`, checkpoint, provider session and sequence numbering; the expired checkpoint, interruption history and capture gap are preserved; interrupted conversation and day-session states return to active as specified; missing audio is never presented as recovered.
- Unexpected disconnection holds the slot for the grace window; expiry marks the stream expired/interrupted, releases the slot, cleans up the provider session, preserves persisted transcripts and surfaces the interruption; a late reconnect receives `stream_expired` and a new stream is required.

**Done when** automated tests (using the fake provider and a controllable clock, with no hard-coded grace duration) show:
1. A second stream is rejected with the clear message; the existing stream's provider session, sequence numbers, checkpoint and transcript persistence are unaffected; simultaneous starts cannot both succeed; a rejected stream persists no data.
2. A valid reconnect within the grace period resumes the existing stream.
3. A reconnect after expiry is rejected with `stream_expired`.
4. An intentionally paused stream remains resumable and is not expired by the grace timer.
5. A wrong-user checkpoint access (resume of another user's `client_stream_id`) is rejected with `stream_not_found` and discloses nothing; an unauthenticated or expired-token reconnect is rejected.
6. An expired stream releases the active-stream slot, so a new stream can start.
7. Existing persisted transcripts remain intact after expiry.
8. No duplicate transcript messages and no sequence-number corruption after resume, replay overlap, duplicate chunks or a half-open socket being replaced.
9. A resume reuses the live provider session and never creates two concurrent provider sessions for one stream.
10. Remote end: the account owner ends a paused stream from a second authenticated session; the checkpoint becomes `ended`, the slot is released, a new stream can then start, and persisted transcripts, bookmarks and edits are unchanged.
11. Remote end authorisation: another user's attempt returns an identical `404` and changes nothing; an unauthenticated or expired-token attempt is rejected; ending an `active` or `reconnect_pending` stream returns `409 stream_not_paused` and the stream continues unaffected; repeating the call is idempotent (`already_ended` / `already_expired`).
12. A remotely ended stream's original device receives `stream_ended` (live socket close or next resume attempt) and is never resumed.
13. Resume/expiry race with a controllable clock: with the clock before, exactly at (expiry wins) and after `grace_expires_at`, and with forced interleavings of the two transactions and of multiple backend instances, exactly one transition wins; if resume wins, a later or stale expiry changes nothing (no gap, no `stream_expired` event, provider session intact); if expiry wins, the late resume receives `stream_expired`, the slot is released, the provider session is cleaned up exactly once, and one gap and one event exist.
14. Session state after expiry: a new stream after expiry has a new `client_stream_id`, sequence numbering starting fresh and a new provider session; the expired checkpoint stays `expired`; the capture gap and `stream_expired` event are preserved (a client-reported and server-detected gap for the same interval merge into one); day-session and conversation statuses follow the design table; no message is back-filled for the gap; message keys never collide across the two streams.
15. Server-side restart rules: a resume of an expired stream is never accepted; a new stream is accepted only through a normal `stream.start`; a stream ended by the user or remotely cannot be resumed or auto-restarted by the server.
16. Capture-gap reconciliation, server gap then client report: after expiry the server-detected gap exists; a later client report with a new `client_gap_id` that overlaps it for the same user and stream with a compatible reason updates that row (no second row), sets `reported_by = both`, records the client's boundaries, refines the estimated start (clamped to the server's start bound) and replaces a generic `network_loss` reason with the client's specific reason.
17. Client report then server detection: the client's gap arrives first; the server's later detection (`server_gap_key`) attaches to the same row and the final boundaries equal those of test 16 with the order reversed (order independence).
18. Duplicate and concurrent reconciliation: repeating the same client report, retrying the same server detection, and running a client report and a server detection concurrently (forced interleavings, multiple backend instances) always leave exactly one row for the gap, with unchanged `sync_rev` on repeats, no unique-constraint failure surfaced to callers, and no deadlock.
19. Distinct gaps stay separate: two gaps in one stream that only touch (`a.end = b.start`) are not merged; same-interval gaps in different streams or for different users are not merged; overlapping gaps with incompatible reasons are not merged; a client report that overlaps two existing compatible gaps is stored separately and the ambiguity metric is recorded; a gap separated by accepted audio is not merged with an earlier gap.
20. Gap closure on first accepted audio: after expiry the open gap is closed when the new stream (identified by `continues_stream_id`, owned by the same user and `expired`) has its first audio accepted; `ended_at` equals the corrected UTC start of that audio and `end_estimated = true`; repeating the closure is a no-op; a later `client_end` earlier than the bound refines the end and sets `end_estimated = false`; a `client_end` later than the bound is clamped to it with `end_estimated = true`; an invalid or other-user `continues_stream_id` is ignored and closes nothing.
21. Boundary rules: with both client and server inputs the canonical start and end follow the stated functions, a computed `ended_at <= started_at` falls back to the server bounds with the conflict metric, and the stored result is identical for every arrival order of the inputs.

## Milestone 3 — Mobile shell, domain and local store
### T3.1 Cross-platform scaffold
Create React Native + TypeScript app and Android/iOS projects.
**Done when:** development builds succeed on both platforms (iOS verified by the owner or macOS CI).

### T3.2 Accessible app shell
Create Sign-in, consent, Home, Recording, Day History, Conversation Detail and Settings screens with loading/empty/error/offline states; set up UI localisation and font scaling.
**Done when:** accessible labels, font scaling (including 200 percent and Indic scripts) and contrast targets are checked.

### T3.3 Domain models
Define the session state machine (native-authoritative projection), native engine interface, platform capability, interruption and gap types, and sync types.
**Done when:** unit tests cover valid/invalid transitions, including interruption versus user pause.

### T3.4 Local store
Select and integrate the SQLite library per T0.2; implement the local schema, encryption, backup exclusion, versioned migrations and wipe on sign-out. **[Approved A2, A12]**
**Done when:** store creation, migration and wipe work on both platforms; no audio or tokens are stored.

### T3.5 Sync engine and pending queue
Implement pull by cursor, idempotent push, queue coalescing, backoff, 401 pause, conflict records and conflict-resolution UI. **[Approved A3, A4]**
**Done when:** the queue survives restart; conflicts never silently overwrite.

### T3.6 Local store and sync tests
Test migrations, corrupt-store rebuild, offline edit/revert/bookmark/rename, conflict scenarios, `cursor_expired` resync, shared search-normalisation vectors, and sign-out with pending operations.
**Done when:** automated tests pass and results are recorded; device-level storage behaviour is verified on physical devices.

## Milestone 4 — Native engines
### T4.1 VAD and chunking design
Choose VAD approach, thresholds, pre-roll/post-roll and chunk size from provider evidence (T0.2); define a bounded replay buffer and measurement plan for its size; plan user evaluation of false negatives. **[Approved A7, A8]**
**Done when:** design note exists with test plan; no audio is persisted.

### T4.2 Android engine
Implement Kotlin capture, VAD, chunking, replay buffer, WebSocket transport, required user-initiated foreground service, permissions (including `POST_NOTIFICATIONS`), persistent notification, pause/resume/stop, route/interruption handling and failure recovery.
**Done when:** physical-device tests pass; no raw audio is written to disk.

### T4.3 iOS engine
Implement Swift capture, VAD, chunking, replay buffer and transport using AVAudioSession/AVAudioEngine or justified equivalent, with permission, lifecycle, interruption and route handling, and permitted background behaviour.
**Done when:** physical iPhone tests pass and interruptions are reported accurately; no raw audio is persisted.

### T4.4 Bridge and contract tests
Test event ordering, bounded buffers, replay, gap events, token handling, JS-suspended behaviour, error propagation and stop semantics on both platforms. Also test the automatic-restart rules: a visible automatic new stream only while capture is still running under the original explicit action, and no restart after an explicit user stop, a remote `stream_ended`, a non-running capture or a rejected restart.
**Done when:** shared contract works while exposing platform differences.

## Milestone 5 — Real ASR and Specific Conversation
### T5.1 Real ASR adapter
Integrate a real provider only for languages with verified status, using consented test audio until retention/training policy is verified. Requires T0.2 and T0.5 findings and explicit owner approval of the provider; does not select a final provider by itself.
**Done when:** adapter tests with recorded evidence pass for each verified language; catalog statuses updated from evidence.

### T5.2 Live captions end to end
Connect the native engine to the backend and render partial/final captions; persist final messages incrementally.
**Done when:** specific conversation works on physical Android and iOS devices.

### T5.3 Specific Conversation lifecycle
Start/pause/resume/stop/save with standalone `local_date` and timezone.
**Done when:** conversation reopens after app restart and appears under the correct date.

## Milestone 6 — Full-Day mode and recovery
### T6.1 DaySession lifecycle
Start/pause/resume/end for `full_day_hybrid`.
**Done when:** statuses and lifecycle events persist correctly.

### T6.2 VAD segmentation integration
Integrate native VAD with configurable silence threshold, grace window, maximum segment duration, lazy conversation creation and VAD-gated transmission. **[Approved A7]**
**Done when:** no empty segments and boundaries are testable/configurable; gating false-negative evaluation recorded.

### T6.3 Manual controls
New Conversation, rename, split and merge from the UI.
**Done when:** timestamps and ordering are preserved.

### T6.4 Recovery and gaps
Handle OS interruption, process termination, network loss, auth expiry and provider failure with visible gaps, haptic/visual alerts and honest state.
**Done when:** confirmed text survives and missing capture intervals are never fabricated; after stream expiry the visible automatic restart, the preserved gap and the separate stream identity behave as specified, and capture is never restarted after an explicit stop.

### T6.5 Rotation, cost and battery
Validate rotation against the real provider limits and measure all-day cost and battery on devices.
**Done when:** measured numbers are documented; no unverified targets are claimed.

## Milestone 7 — History and transcript tools
### T7.1 Day history
Group by stored local date/timezone for days and standalone conversations.
**Done when:** timezone/date-boundary tests pass.

### T7.2 Transcript detail
Render timestamped messages, gap markers, edited/original indicators and provisional/final states.
**Done when:** long transcripts remain performant and accessible.

### T7.3 User tools
Edit/revert, bookmark, search (server and offline), export and delete.
**Done when:** persistence, ownership, cascade deletion and offline behaviour tests pass.

### T7.4 Account lifecycle
Account deletion flow, sign-out with pending-operation warning and consent re-prompt.
**Done when:** server data, Firebase user and local data are removed in tests.

## Milestone 8 — Hardening
### T8.1 Accessibility audit
Test screen readers, font scaling, contrast, focus order, control size, live-region policy and Indic-script rendering with target users.
**Done when:** critical findings are resolved or documented with mitigation.

### T8.2 Privacy/security audit
Review audio retention (including replay buffer and provider), logs, credentials, TLS, token handling, authorization, local-store protections, deletion and backups.
**Done when:** no raw audio persistence or credential leakage; critical/high findings resolved.

### T8.3 Language evaluation
Test verified languages with representative consented samples, Indian accents, noise and code-switching. Document measured correction/quality metrics.
**Done when:** language support status and limitations are published; unsupported languages are not advertised.

## Milestone 9 — Release readiness
### T9.1 Staging
Prepare secrets, IAM, migrations, monitoring, cost alerts and rollback. Cloud vendor and region are decided before this milestone.
**Done when:** staging and rollback are documented; production requires explicit approval.

### T9.2 Internal builds
Prepare Android/iOS signing and privacy/microphone disclosures.
**Done when:** internal builds install and pass device matrix.

### T9.3 Handover
Document setup, environment, migrations, tests, devices, languages, limitations and incident process.
**Done when:** every completion claim maps to test evidence.

## Definition of done for every task
- Acceptance criteria met.
- Automated tests run.
- Physical-device test performed for hardware/lifecycle features.
- Loading, empty, offline and error states handled.
- Accessibility and privacy reviewed.
- No secrets, raw audio or unnecessary transcript content in logs.
- Documentation and task status updated.

## Task ID mapping (previous to current)
| Previous | Current |
|---|---|
| T0.1, T0.2, T0.4 | T0.1, T0.2, T0.4 (T0.2 extended) |
| T0.3 (create steering) | T0.3 (verify steering, create structure) |
| T1.1 | T3.1 |
| T1.2 | T3.2 |
| T1.3 | T3.3 |
| T2.1 | T4.2 |
| T2.2 | T4.3 |
| T2.3 | T4.4 |
| T3.1 | T1.2 |
| T3.2 | T1.3 |
| T3.3 | T1.5 |
| T4.1 | T2.1 |
| T4.2 | T2.2 (fake) and T5.1 (real) |
| T4.3 | T5.2 |
| T5.1 | T5.3 |
| T5.2 | T6.1 |
| T5.3 | T4.1 (design) and T6.2 (integration) |
| T5.4 | T6.3 |
| T5.5 | T6.4 |
| T6.1, T6.2, T6.3 | T7.1, T7.2, T7.3 |
| T7.1, T7.2, T7.3 | T8.1, T8.2, T8.3 |
| T8.1, T8.2, T8.3 | T9.1, T9.2, T9.3 |
| New | T0.5, T1.1, T1.4, T1.6, T1.7, T1.8, T2.3–T2.6, T3.4–T3.6, T6.5, T7.4 |

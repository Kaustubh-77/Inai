# Inai MVP — Requirements

Items marked **[Approved Ax]** are amendment decisions approved by the owner on 2026-11-25 (A1–A14). Items marked **[Unverified]** depend on the validation gate (T0.2).

## Overview and decisions
Inai converts spoken conversation into timestamped text for deaf and hard-of-hearing users. Platforms: Android and iOS. Initial target languages: Tamil (`ta`), Kannada (`kn`), Malayalam (`ml`), Telugu (`te`), Hindi (`hi`) and English (`en`), subject to verified streaming support. Full-day mode is hybrid. Audio retention is text only. Segmentation is auto-manual.

Approved decisions: (1) native Kotlin/Swift owns audio capture, VAD, chunking and streaming transport, with React Native owning UI, session presentation and transcript events; (2) `original_text` and `edited_text` are stored separately; (3) Firebase Authentication with server-side ID token verification; (4) SQLite for offline reading and editing of previously synchronised transcripts with pending edit synchronisation; (5) Sarvam AI is the first ASR candidate to evaluate and is not selected.

## Functional requirements

### FR-01 Onboarding and permissions
- Explain microphone use before requesting permission.
- Request permission in context of a user-initiated recording flow.
- Provide recovery instructions for denial or revocation.
- Explain visible recording and text-only retention.
- Show the privacy and recording-responsibility notices and record acknowledgement (see FR-12).

### FR-02 Language settings
- Let users select a preferred language only from the verified-language catalog served by the backend.
- The catalog maps each app language code to a provider and provider locale, with a verification status and evidence reference. Only entries with a verified streaming status are offered.
- No default language is assumed. The preferred language is unset until the user chooses. (Changed from the previous default of `ta`; see design §5.)
- If no language is verified for the active provider, recording is disabled with an honest explanation.
- Do not advertise a language as supported until provider/region support is confirmed.
- Preserve provider-returned language metadata on each message.
- Mixed-language recognition is a quality goal, not a guarantee.

### FR-03 Specific Conversation
- User can explicitly start, pause, resume and stop.
- Show recording state and elapsed time.
- Display partial captions as provisional and final captions as confirmed.
- Persist final transcript entries incrementally (server-side, by the backend).
- Allow naming and renaming.
- A specific conversation is standalone (not part of a DaySession) and carries its own local date and timezone for day-wise history.
- Only one capture runs at a time. Starting a specific conversation while a day is active is not allowed; use New Conversation inside the day instead.

### FR-04 Full-Day mode
- User explicitly starts a DaySession. The only MVP mode is `full_day_hybrid` (VAD suggestions plus manual controls). The undefined `mixed` mode is removed (see design §10).
- A DaySession contains zero or more Conversations.
- Support pause, resume, manual New Conversation and End Day.
- Native VAD proposes speech segments and boundaries. When auto-segmentation is enabled the boundary is applied automatically; otherwise it is recorded but not applied.
- Silence is not an infallible conversation boundary.
- Do not create empty conversations; the next conversation is created on the first accepted speech content.
- Represent OS/network interruptions honestly as capture gaps (FR-09).
- **[Approved A7]** Audio is transmitted only while VAD detects speech (with pre-roll and post-roll) to limit cost and battery.

### FR-05 Segmentation correction
- Rename, split and merge conversations.
- Preserve message timestamps and chronological order.
- Split and merge never change message identity or de-duplication keys.
- Merge is allowed only between conversations in the same DaySession, or between standalone conversations on the same local date **[Approved A5]**.
- Record meaningful manual segmentation actions.
- Split and merge require connectivity (FR-13).

### FR-06 Transcript
- Messages contain original text, optional edited text, timestamps, timestamp source and original language when available.
- Speaker labels are optional and never fabricated.
- Partial and final states are visually distinct. Partial text is never persisted.
- The user can correct a message. The correction is stored as `edited_text`. `original_text` is immutable. The user can revert a correction.
- Displayed text is `edited_text` when present, otherwise `original_text`. Export and search use displayed text; export can optionally include original text.
- Bookmark messages with an optional note.
- Translation, if added, must not overwrite original or edited text.
- Transcript timelines include capture-gap markers in chronological position.

### FR-07 History and search
- Show day-wise history using stored local date and timezone, including standalone conversations under their own date.
- Show conversation threads in chronological order.
- Show timestamped chat-like transcript detail.
- Search only the authenticated user's own transcript content, online on the server and offline in the local store (previously synchronised data only).
- Search must match substrings in Latin, Devanagari, Tamil, Telugu, Kannada and Malayalam text using a documented normalisation (Unicode NFC, joiner handling, case folding). The same normalisation is applied on the server and device, verified with shared test vectors.
- The search implementation is chosen by a validation spike with per-script test corpora (T1.1). Stemming is not required.
- Paginate or virtualise long transcript lists.

### FR-08 Export and deletion
- Export a conversation transcript in a documented text format.
- Delete individual conversations or an entire day and its children. Deleted content is purged immediately; only content-free tombstones remain for sync.
- Document backup retention and deletion behaviour.
- Account deletion is specified in FR-12.

### FR-09 Streaming, timing and recovery
- Use authenticated TLS streaming. Credentials are sent in the first message, never in the URL.
- Sequence audio chunks and acknowledge accepted data. Native replays unacknowledged chunks within a bounded in-memory replay window after reconnect **[Approved A8]**.
- Prevent duplicate final messages after retry.
- Handle network loss, reconnect, provider timeout and throttling.
- **Capture gaps:** record any interval where audio was lost or not processed because of OS interruption, network loss beyond the replay window, permission revocation, audio route-change failure, process termination, auth expiry or provider failure. User pauses are not gaps. Gaps are visible, stored, synchronised and never filled with fabricated text.
- Warn when speech may not have been processed.
- Persist confirmed transcript messages incrementally.
- **Timestamps:** message times derive from native capture offsets mapped to UTC, with server correction for client clock skew. Each message records a `timestamp_source`; approximate timing is not presented as exact.
- **Provider session rotation:** the server rotates provider sessions to respect provider duration and idle limits **[Unverified]** without losing or duplicating speech, preferring silence boundaries, and records rotations and any resulting gaps.
- **One active stream per user [Approved A11].** If a second stream is requested while one is active, the new stream is rejected and the user sees a clear message that another recording is already active. The existing stream is never terminated or superseded and continues unaffected. A reconnect using the existing `client_stream_id` is a resume, not a second stream.
- A rejected stream sends no audio to any provider, persists no transcript data and creates no capture gap or lifecycle event on the existing stream.
- **Resume and ownership [Approved A11 clarification]:** every reconnect requires Firebase authentication. The server verifies that the authenticated user owns the existing stream checkpoint; a resume for a checkpoint the user does not own is rejected without revealing whether it exists. `client_stream_id` is an identifier, never an authentication credential. A valid resume continues the existing checkpoint and sequence numbering without creating a second provider session or duplicating transcript messages.
- **Intentional pause:** an explicit user pause remains resumable. The unexpected-disconnection grace timer does not apply to an intentionally paused stream. The user can explicitly resume or stop it.
- **Unexpected disconnection:** the stream keeps its active-stream slot for a finite, configurable reconnect grace window. The initial value is an implementation/configuration decision that requires reconnect testing and is not fixed by this specification. A successful reconnect within the window resumes the existing stream.
- **Paused-stream recovery:** a paused stream holds the active-stream slot indefinitely unless explicitly ended; this specification sets no pause timeout. The account owner can explicitly end their paused stream from another authenticated session or device. The server verifies ownership, rejects any other user without disclosing the stream, ends only a `paused` stream, marks the checkpoint ended, releases the slot and preserves all persisted transcripts. The user sees a confirmation before ending and a clear outcome afterwards. A live or reconnecting stream cannot be ended this way.
- **Resume/expiry race:** if a valid resume and an expiry happen concurrently, exactly one transition wins atomically. A successful resume prevents the checkpoint from being expired afterwards. If expiry wins, the late resume receives `stream_expired`.
- **Session state after expiry:** when a new stream starts after an expiry, the interrupted conversation and day session return to active, with the interruption history and the capture gap preserved. The missing audio is never presented as recovered. The new stream has its own identity, checkpoint, provider session and sequence numbering.
- **Automatic restart:** a new stream may start automatically only while native capture is still running under the user's original explicit recording action. The interruption and the new stream are visible to the user. Capture is never restarted after the user explicitly stopped it or after the stream was ended from another device.
- **Expiry:** when the window expires the stream is marked expired and interrupted, its active-stream slot is released and its provider session is cleaned up. All previously persisted transcript data is preserved, and the interruption is shown to the user. A later reconnect receives a clear `stream_expired` response and must start a new stream; an expired live stream is never silently resumed.

### FR-10 Platform recording
- Android follows current microphone permission and foreground-service rules, including `POST_NOTIFICATIONS` for the persistent notification, and starts capture only from a visible user-initiated state.
- iOS follows current microphone, AVAudioSession and permitted background audio rules.
- The native engine runs independently of JS liveness. JS can re-attach to engine status.
- Expose platform capabilities and interruption states, including whether the platform can resume automatically or requires a user action.
- Do not promise unrestricted background recording.
- Validate hardware behaviour on physical devices.

### FR-11 Privacy and accessibility
- Recording begins only after explicit action and remains visibly indicated.
- Raw audio is not persisted by default, including in the replay buffer and local store.
- Logs do not contain raw audio, secrets or full transcript content by default.
- Caption size is adjustable (up to at least 200 percent); high contrast and screen-reader support are provided.
- Interruptions, gaps and errors are signalled visually and with haptics; never audio-only.
- Partial captions are never announced by screen readers; finals are announced politely and configurably.
- Numeric targets: text contrast at least 4.5:1 (7:1 in high-contrast mode); touch targets at least 48 dp/44 pt, with pause/stop at least 56 dp/pt. Targets are validated with users.
- Before any real user audio is sent to a provider, the provider's retention and training policy must be verified and recorded.

### FR-12 Authentication and account
- Sign in with Firebase Authentication. Sign-in methods are an open decision.
- The backend verifies the Firebase ID token (signature, issuer, audience, expiry) on every REST request and on WebSocket authentication, and derives identity only from the verified subject.
- Provision the user record on first verified request.
- WebSocket authentication occurs in the first message with in-band token refresh before expiry **[Approved A1]**.
- Record consent acknowledgements with version and time; re-prompt when versions change.
- Account deletion removes all server-side data and the Firebase user and wipes the local store. The user is warned about unsynchronised edits before sign-out or deletion.
- Sign-out wipes the local store **[Approved A12]**.

### FR-13 Offline storage and synchronisation
- Previously synchronised transcripts are available offline for reading, searching, editing, reverting, bookmarking and renaming. Offline recording is not supported.
- Offline operations are queued with idempotency keys and survive app restart.
- Split, merge, delete and export require connectivity so confirmation is truthful **[Approved A3]**.
- Sync pulls changes by a per-user revision cursor and pushes queued operations idempotently.
- Text edits and renames use compare-and-set against the last known server value. A mismatch is a conflict that is shown to the user with both versions; neither is silently overwritten **[Approved A4]**.
- Bookmark add/remove is idempotent. Deleted or merged targets produce a visible failed-operation result.
- If a cursor is older than the tombstone retention window the client performs a full resync.
- The local store is encrypted at rest, excluded from device backups and never stores audio **[Approved A2]**.
- The local store has versioned migrations; a corrupt store can be rebuilt from the server, with a warning about unsynchronised edits.

### FR-14 UI localisation and alerts
- The app UI supports localisation; initial UI locales are an open decision.
- Scripts used for captions render without clipping or broken shaping at large font scales.
- Interruption and gap alerts follow FR-11.

## Non-functional requirements
- Reliability: confirmed transcript entries survive app restart and supported reconnect flows. Queued offline edits survive restart.
- Performance: measure caption latency; do not claim unverified targets.
- Security: all data operations are user scoped, enforced in services and in database constraints.
- Maintainability: ASR provider is isolated behind an adapter.
- Portability: shared app code does not erase native platform differences.
- Observability: collect safe operational metadata only (latency, reconnects, rotations, gap counts, provider errors).
- Cost: full-day streaming cost and battery use are measured before release.
- API conventions: cursor pagination, a consistent problem-details error model with stable error codes, and idempotency keys on mutating requests.

## Acceptance criteria
1. Specific recording works on supported physical Android and iOS devices.
2. Partial and final caption states are distinguishable.
3. Final transcript entries persist incrementally.
4. A day can contain multiple conversation threads.
5. VAD proposes boundaries; user can manually create, split, merge and rename.
6. Silence does not create empty conversations.
7. Day grouping follows stored local date and timezone, for days and standalone conversations.
8. User can edit, bookmark, search, export and delete.
9. Permission denial, OS interruption and network loss are communicated truthfully.
10. No raw audio is persisted in app storage, database, object storage or logs.
11. Each target language has provider capability and test evidence before being advertised as supported.
12. Accessibility is reviewed with assistive technology and target-user feedback.
13. Editing never changes `original_text`; revert restores display of the original.
14. Language list shown to users contains only verified catalog entries; no default language is preselected.
15. Requests with invalid, expired, wrong-audience or missing Firebase tokens are rejected on REST and WebSocket, and no token appears in URLs or logs.
16. Offline edit, bookmark and rename survive restart and sync once online; conflicts are surfaced and no edit is silently lost.
17. Capture gaps from OS interruption, network loss and provider failure appear in the transcript and are never filled with invented text.
18. Split and merge preserve message timestamps, ordering, bookmarks and de-duplication; retried finals do not duplicate after split or merge.
19. Message timestamps carry a timestamp source and remain correct across pauses, reconnects and provider session rotation.
20. Substring search works for Latin, Devanagari, Tamil, Telugu, Kannada and Malayalam corpora on server and device with identical normalisation results.
21. Account deletion removes server data, the Firebase user and local data.
22. The account owner can end a paused stream from another device; no other user can; the slot is released and persisted transcripts are unchanged.
23. A concurrent resume and expiry produce exactly one outcome, and a stream expired and replaced by a new stream keeps its gap and interruption history with separate stream identity and sequence numbering.

## Open validation items
- Confirm provider streaming support for all six languages in the selected region (Sarvam AI is the first candidate; no provider is selected).
- Verify provider timestamps and offsets, stream duration and idle limits, audio format, partial-result behaviour, quotas, pricing, and audio retention/training policy.
- Evaluate Indian accents, noise and code-switching with consented representative samples.
- Confirm Android/iOS background behaviour by OS version and device.
- Confirm that native Firebase SDK sessions give the native engine background token refresh; otherwise define the fallback behaviour.
- Choose the SQLite library and verify encryption, FTS tokenizers and backup exclusion.
- Run the Indic-script search spike.
- Obtain legal/privacy review of consent and disclosure wording, including bystander recording rules.

## Requirements changed or removed, with reasons
- Language default `ta` and `enabled_languages` (design) removed: contradicted FR-02's rule not to advertise unverified languages.
- FR-03 and FR-09 "persist final transcript entries incrementally" retained, clarified as server-side.
- `subscribeToAudioFrames` interface (steering/design) removed: native now owns VAD, chunking and transport.
- `mixed` day-session mode removed: undefined and unreferenced by any requirement.
- Single `text` column replaced by `original_text` plus `edited_text`: edits previously destroyed the original, contradicting FR-06.
- Per-conversation de-duplication replaced by user-scoped immutable keys: previous design could collide on merge.

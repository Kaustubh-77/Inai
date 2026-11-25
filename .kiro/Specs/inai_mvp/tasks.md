# Inai MVP — Implementation Tasks

## Working rules
Work in small increments. Read steering and Spec files before each task. Add tests and documentation with each vertical slice. Do not mark work complete unless tests/builds were run. Do not deploy paid resources or publish builds without explicit approval.

## Milestone 0 — Foundation
### T0.1 Repository/toolchain inspection
Inspect repository, Kiro conventions, Node/package manager, React Native build approach, Python, PostgreSQL and native build prerequisites. Document setup.
**Done when:** reproducible local setup guide exists; architecture is reviewed before implementation.

### T0.2 Platform and provider validation
Verify current Android microphone/foreground-service rules, iOS microphone/AVAudioSession/background rules, React Native native module support, and streaming ASR support for `ta`, `kn`, `ml`, `te`, `hi`, `en` in the intended region. Record source URLs, date, limitations, pricing and quotas.
**Done when:** capability matrix exists and unsupported assumptions are not hard-coded.

### T0.3 Steering and structure
Create product, architecture, coding standards, privacy/accessibility and platform constraints steering files plus app/backend/infra/docs structure.
**Done when:** files are committed and align with approved architecture.

### T0.4 Quality baseline
Configure formatting, lint, type checks and test commands.
**Done when:** baseline checks run locally and in CI.

## Milestone 1 — Shared mobile foundation
### T1.1 Cross-platform scaffold
Create React Native + TypeScript app and Android/iOS projects.
**Done when:** development builds succeed on both platforms.

### T1.2 Accessible app shell
Create Home, Recording, Day History, Conversation Detail and Settings screens with loading/empty/error states.
**Done when:** accessible labels and font scaling are checked.

### T1.3 Domain models
Define session state machine, native recording interface, platform capability and interruption types.
**Done when:** unit tests cover valid/invalid transitions.

## Milestone 2 — Native recording
### T2.1 Android adapter
Implement Kotlin capture and required user-initiated foreground service, permissions, persistent notification, pause/resume/stop, route/interruption handling and failure recovery.
**Done when:** physical-device tests pass; no raw audio is written to disk.

### T2.2 iOS adapter
Implement Swift capture using AVAudioSession/AVAudioEngine or justified equivalent, permission, lifecycle, interruption and route handling, and permitted background behaviour.
**Done when:** physical iPhone tests pass and interruptions are reported accurately; no raw audio is persisted.

### T2.3 Bridge tests
Test event ordering, bounded buffers, error propagation and stop semantics on both platforms.
**Done when:** shared contract works while exposing platform differences.

## Milestone 3 — Backend and database
### T3.1 Migrations/models
Implement users, settings, day_sessions, conversations, transcript_messages, bookmarks, session_events and stream_checkpoints.
**Done when:** migrations and rollback tests pass.

### T3.2 Authentication/ownership
Implement trusted authentication and enforce ownership on all repositories/routes.
**Done when:** cross-user access tests fail safely.

### T3.3 REST APIs
Implement session, conversation, transcript edit, search, export and deletion APIs.
**Done when:** API tests cover success, validation and ownership failures.

## Milestone 4 — Streaming
### T4.1 WebSocket protocol
Implement versioned events, sequence numbers, acknowledgements, idempotency and bounded queues.
**Done when:** ordering, duplicate and reconnect tests pass.

### T4.2 ASR adapter
Implement provider-neutral interface and fake provider. Integrate real ASR only after language/region verification.
**Done when:** partial, final, timeout, throttling and failure tests pass.

### T4.3 Live captions
Connect native frames to backend and render partial/final captions; persist final messages incrementally.
**Done when:** specific conversation works on physical Android and iOS devices.

## Milestone 5 — Sessions and segmentation
### T5.1 Specific Conversation
Start/pause/resume/stop/save.
**Done when:** conversation reopens after app restart.

### T5.2 DaySession lifecycle
Start/pause/resume/end.
**Done when:** statuses and lifecycle events persist correctly.

### T5.3 VAD segmentation
Implement speech activity, configurable silence threshold, grace window and max segment duration.
**Done when:** no empty segments and boundaries are testable/configurable.

### T5.4 Manual controls
New Conversation, rename, split and merge.
**Done when:** timestamps and ordering are preserved.

### T5.5 Recovery
Handle OS interruption, process termination and network loss.
**Done when:** confirmed text survives and missing capture intervals are never fabricated.

## Milestone 6 — History and transcript tools
### T6.1 Day history
Group by stored local date/timezone.
**Done when:** timezone/date-boundary tests pass.

### T6.2 Transcript detail
Render timestamped messages and provisional/final states.
**Done when:** long transcripts remain performant and accessible.

### T6.3 User tools
Edit, bookmark, search, export and delete.
**Done when:** persistence, ownership and cascade deletion tests pass.

## Milestone 7 — Hardening
### T7.1 Accessibility audit
Test screen readers, font scaling, contrast, focus order and control size with target users.
**Done when:** critical findings are resolved or documented with mitigation.

### T7.2 Privacy/security audit
Review audio retention, logs, credentials, TLS, authorization, deletion and backups.
**Done when:** no raw audio persistence or credential leakage; critical/high findings resolved.

### T7.3 Language evaluation
Test verified languages with representative consented samples, Indian accents, noise and code-switching. Document measured correction/quality metrics.
**Done when:** language support status and limitations are published; unsupported languages are not advertised.

## Milestone 8 — Release readiness
### T8.1 Staging
Prepare secrets, IAM, migrations, monitoring, cost alerts and rollback.
**Done when:** staging and rollback are documented; production requires explicit approval.

### T8.2 Internal builds
Prepare Android/iOS signing and privacy/microphone disclosures.
**Done when:** internal builds install and pass device matrix.

### T8.3 Handover
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

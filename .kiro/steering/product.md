# Inai — Product Steering

## Identity
- Name: Inai
- Promise: Every conversation deserves to be understood.
- Product: Accessibility-first speech-to-text companion for deaf and hard-of-hearing people.
- Platforms: Android and iOS.
- Initial target languages: Tamil (`ta`), Kannada (`kn`), Malayalam (`ml`), Telugu (`te`), Hindi (`hi`) and English (`en`), subject to provider validation. No language is advertised or selectable until it is marked verified in the server language catalog.

## Final decisions
- Full-day mode: hybrid automatic speech detection plus manual controls.
- Audio retention: transcript text only; raw audio is transient and never persisted by default.
- Segmentation: automatic suggestions plus manual New Conversation, split, merge and rename.
- Platform: cross-platform, with native capture implementations per OS.

### Approved decisions (2026-11 amendment, approved 2026-11-25; amendments A1–A14 in the spec files)
1. Native Kotlin/Swift owns audio capture, VAD, chunking and streaming transport. React Native handles UI, session presentation and transcript events.
2. Transcripts preserve `original_text` and `edited_text` separately.
3. Firebase Authentication for the MVP, with server-side Firebase ID token verification.
4. SQLite on device for offline reading and editing of previously synchronised transcripts, with pending edit synchronisation.
5. Sarvam AI is the first ASR provider candidate to evaluate. It is **not** selected or confirmed.

## Product principles
1. Recording starts only after explicit user action.
2. Recording state is clearly visible and pause/stop are easy to access.
3. Original transcript text is preserved. User corrections are stored separately and never overwrite the original; translation, if added, is also separate.
4. Partial hypotheses are clearly provisional; final text is confirmed.
5. Do not promise perfect transcription, speaker identification or uninterrupted background capture.
6. Users can correct transcript text and segmentation.
7. Accessibility and privacy are product requirements, not post-launch polish.
8. Gaps in capture are shown honestly in the transcript. Missing speech is never invented or hidden.
9. Interruptions are signalled visually and by haptics, because users cannot rely on sound.

## MVP
- Sign-in (Firebase), account deletion, and consent acknowledgement.
- Onboarding and microphone permission explanation.
- Language and accessibility settings; languages offered only if verified.
- Specific Conversation: start, pause, resume, stop, live captions and save.
- Full-Day: start day, VAD-based segments, manual boundary controls, pause/resume/end.
- Day-wise history with multiple chat-like conversation threads; standalone conversations appear under their own date.
- Timestamped transcript detail, edit (with revert to original), rename, bookmark, search (including Tamil, Telugu, Kannada and Malayalam text), export, split, merge and delete.
- Offline reading, search and editing of previously synchronised transcripts, with queued edit sync and explicit conflict resolution.
- Capture gaps shown inline in the transcript.
- Network interruption and session recovery.
- Localised app UI (initial UI locales to be decided).
- Android and iOS physical-device test plans.

## Non-goals
- Sign-language recognition in MVP.
- Covert recording or raw audio archival.
- Voice cloning or biometric speaker identification.
- Guaranteed perfect transcription or translation.
- Claiming a language is supported before streaming capability and quality are validated.
- Offline recording or on-device speech recognition in the MVP (recording needs connectivity to the ASR service).
- Offline split, merge, delete or export in the MVP.
- Selecting a final ASR provider before the validation gate is passed.

## Core journeys
### Sign-in
Install → onboarding → sign in → consent acknowledgement → permission explanation when the user first starts recording.

### Specific conversation
Start → permission check → choose verified language → visible capture → live partial/final captions → stop → save → review/edit.

### Full-day
Start My Day → visible capture → VAD proposes segments → manual New Conversation/pause/resume → End Day → review day-wise threads. If capture is interrupted, the gap is visible and the user is alerted; resuming may require a user action.

### Offline review
Open a previously synchronised conversation without connectivity → read, search, edit or bookmark → edits queue and sync when online; conflicts are shown for the user to resolve.

## Success criteria
- Specific recording works on supported physical Android and iOS devices.
- A day session contains multiple conversation records.
- Confirmed transcript messages persist incrementally.
- Day grouping follows stored local date and timezone, for both day sessions and standalone conversations.
- OS/network interruptions are represented honestly as capture gaps.
- Original transcript text is never lost by editing.
- Offline edits survive restart and synchronise without silent overwrite.
- No raw audio is persisted in app storage, database, object storage or logs.
- Six target languages have a documented provider support and quality status; only verified languages are offered.
- Deaf and hard-of-hearing users review usability and caption readability.

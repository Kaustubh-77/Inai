# Inai — Product Steering

## Identity
- Name: Inai
- Promise: Every conversation deserves to be understood.
- Product: Accessibility-first speech-to-text companion for deaf and hard-of-hearing people.
- Platforms: Android and iOS.
- Initial target languages: Tamil (`ta`), Kannada (`kn`), Malayalam (`ml`), Telugu (`te`), Hindi (`hi`) and English (`en`), subject to provider validation.

## Final decisions
- Full-day mode: hybrid automatic speech detection plus manual controls.
- Audio retention: transcript text only; raw audio is transient and never persisted by default.
- Segmentation: automatic suggestions plus manual New Conversation, split, merge and rename.
- Platform: cross-platform, with native capture implementations per OS.

## Product principles
1. Recording starts only after explicit user action.
2. Recording state is clearly visible and pause/stop are easy to access.
3. Original transcript text is preserved; translation, if added, is separate.
4. Partial hypotheses are clearly provisional; final text is confirmed.
5. Do not promise perfect transcription, speaker identification or uninterrupted background capture.
6. Users can correct transcript text and segmentation.
7. Accessibility and privacy are product requirements, not post-launch polish.

## MVP
- Onboarding and microphone permission explanation.
- Language and accessibility settings.
- Specific Conversation: start, pause, resume, stop, live captions and save.
- Full-Day: start day, VAD-based segments, manual boundary controls, pause/resume/end.
- Day-wise history with multiple chat-like conversation threads.
- Timestamped transcript detail, edit, rename, bookmark, search, export, split, merge and delete.
- Network interruption and session recovery.
- Android and iOS physical-device test plans.

## Non-goals
- Sign-language recognition in MVP.
- Covert recording or raw audio archival.
- Voice cloning or biometric speaker identification.
- Guaranteed perfect transcription or translation.
- Claiming a language is supported before streaming capability and quality are validated.

## Core journeys
### Specific conversation
Start → permission check → choose language → visible capture → live partial/final captions → stop → save → review/edit.

### Full-day
Start My Day → visible capture → VAD proposes segments → manual New Conversation/pause/resume → End Day → review day-wise threads.

## Success criteria
- Specific recording works on supported physical Android and iOS devices.
- A day session contains multiple conversation records.
- Confirmed transcript messages persist incrementally.
- Day grouping follows stored local date and timezone.
- OS/network interruptions are represented honestly.
- No raw audio is persisted in app storage, database, object storage or logs.
- Six target languages have a documented provider support and quality status.
- Deaf and hard-of-hearing users review usability and caption readability.

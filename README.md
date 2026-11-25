# Inai - AI-Powered Communication assistant for Deaf people


# INAI (இணை).

**Making everyday conversations more accessible through real-time speech-to-text.**

Inai is an accessibility-first mobile application designed to help deaf and hard-of-hearing individuals understand spoken conversations through live transcription.

## Key Features

- **Real-time transcription:** Convert speech into readable text.
- **Multilingual support:** Targeting Tamil, Telugu, Kannada, Malayalam, Hindi, and English. A language is offered only after its streaming support is verified.
- **Conversation management:** Start, pause, resume, split, merge, and organize conversations.
- **Daily history:** Access conversations organized by date, with individual timestamps.
- **Hybrid full-day mode:** Combine automatic voice activity detection (VAD) with manual recording controls.
- **Transcript corrections:** Edit text without losing the original, and revert at any time.
- **Offline access:** Read, search, and edit previously synchronised transcripts offline, with edits synchronised later.
- **Honest capture gaps:** Interruptions and lost audio are shown in the transcript instead of being hidden.
- **Accessibility:** Adjustable text size, high contrast, and screen-reader support.

## Technology Stack

| Component | Technology |
|---|---|
| Mobile | React Native + TypeScript |
| Android audio engine | Kotlin |
| iOS audio engine | Swift |
| Local storage | SQLite (offline transcripts and pending edits) |
| Authentication | Firebase Authentication, verified server-side |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Real-time communication | WebSockets |
| Speech recognition | Streaming ASR provider (not yet selected; Sarvam AI is the first candidate under evaluation) |

## Architecture

Inai uses native audio engines on Android and iOS. Each engine owns audio capture, voice activity detection, chunking and streaming to the backend, so raw audio never passes through JavaScript. React Native handles the user interface, session presentation and transcript events. A FastAPI backend handles real-time communication, speech recognition integration, and transcript management.

## Privacy First

- Audio is processed transiently and not stored by default, including on the device.
- Transcripts are stored as text. Original text and user edits are kept separately.
- Recording requires explicit user action.
- Users remain in control of recording and their saved conversations, including export and deletion.
- Real user audio is not sent to any speech provider until its retention and training policy has been verified.

## Development Status

Currently in the specification and architecture phase. The specification amendments (A1–A14) were approved on 2026-11-25. Implementation has not started. Development will proceed incrementally, beginning with platform and provider validation, then the backend and streaming protocol, before native audio engines, live transcription, conversation history and hybrid full-day recording. See `.kiro/specs/inai-mvp/` for requirements, design and tasks.


**Vision:** Building a more inclusive world where language and hearing barriers don't limit everyday communication.

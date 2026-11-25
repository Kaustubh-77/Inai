# Inai - AI-Powered Communication assistant for Deaf people


# INAI (இணை).

**Making everyday conversations more accessible through real-time speech-to-text.**

Inai is an accessibility-first mobile application designed to help deaf and hard-of-hearing individuals understand spoken conversations through live transcription.

## Key Features

- **Real-time transcription:** Convert speech into readable text.
- **Multilingual support:** Targeting Tamil, Telugu, Kannada, Malayalam, Hindi, and English.
- **Conversation management:** Start, pause, resume, split, merge, and organize conversations.
- **Daily history:** Access conversations organized by date, with individual timestamps.
- **Hybrid full-day mode:** Combine automatic voice activity detection (VAD) with manual recording controls.
- **Accessibility:** Adjustable text size, high contrast, and screen-reader support.

## Technology Stack

| Component | Technology |
|---|---|
| Mobile | React Native + TypeScript |
| Android | Kotlin |
| iOS | Swift |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Real-time communication | WebSockets |
| Speech recognition | Streaming ASR provider |

## Architecture

Inai uses native audio capture on Android and iOS, with a FastAPI backend handling real-time communication, speech recognition integration, and transcript management.

## Privacy First

- Audio is processed transiently and not stored by default.
- Transcripts are stored as text.
- Recording requires explicit user action.
- Users remain in control of recording and their saved conversations.

## Development Status

Currently in the specification and architecture phase. Development will proceed incrementally, beginning with live transcription and conversation history before introducing hybrid full-day recording.


**Vision:** Building a more inclusive world where language and hearing barriers don't limit everyday communication.

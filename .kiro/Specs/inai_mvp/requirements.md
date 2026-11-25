# Inai MVP — Requirements

## Overview and decisions
Inai converts spoken conversation into timestamped text for deaf and hard-of-hearing users. Platforms: Android and iOS. Initial target languages: Tamil (`ta`), Kannada (`kn`), Malayalam (`ml`), Telugu (`te`), Hindi (`hi`) and English (`en`), subject to verified streaming support. Full-day mode is hybrid. Audio retention is text only. Segmentation is auto-manual.

## Functional requirements

### FR-01 Onboarding and permissions
- Explain microphone use before requesting permission.
- Request permission in context of a user-initiated recording flow.
- Provide recovery instructions for denial or revocation.
- Explain visible recording and text-only retention.

### FR-02 Language settings
- Let users select a preferred language from verified live-supported languages.
- Do not advertise a language as supported until provider/region support is confirmed.
- Preserve provider-returned language metadata.
- Mixed-language recognition is a quality goal, not a guarantee.

### FR-03 Specific Conversation
- User can explicitly start, pause, resume and stop.
- Show recording state and elapsed time.
- Display partial captions as provisional and final captions as confirmed.
- Persist final transcript entries incrementally.
- Allow naming and renaming.

### FR-04 Full-Day mode
- User explicitly starts a DaySession.
- A DaySession contains zero or more Conversations.
- Support pause, resume, manual New Conversation and End Day.
- VAD proposes speech segments and boundaries.
- Silence is not an infallible conversation boundary.
- Do not create empty conversations.
- Represent OS/network interruptions honestly.

### FR-05 Segmentation correction
- Rename, split and merge conversations.
- Preserve message timestamps and chronological order.
- Record meaningful manual segmentation actions.

### FR-06 Transcript
- Messages contain text, timestamps and original language when available.
- Speaker labels are optional and never fabricated.
- Partial and final states are visually distinct.
- User can correct text and bookmark messages.
- Translation, if added, must not overwrite original text.

### FR-07 History
- Show day-wise history using stored local date and timezone.
- Show conversation threads in chronological order.
- Show timestamped chat-like transcript detail.
- Search only the authenticated user's own transcript content.
- Paginate or virtualise long transcript lists.

### FR-08 Export and deletion
- Export a conversation transcript in a documented text format.
- Delete individual conversations or an entire day and its children.
- Document backup retention and deletion behaviour.

### FR-09 Streaming and recovery
- Use authenticated TLS streaming.
- Sequence audio chunks and acknowledge accepted data.
- Prevent duplicate final messages after retry.
- Handle network loss, reconnect, provider timeout and throttling.
- Warn when speech may not have been processed.
- Persist confirmed transcript messages incrementally.

### FR-10 Platform recording
- Android follows current microphone permission and foreground-service rules.
- iOS follows current microphone, AVAudioSession and permitted background audio rules.
- Expose platform capabilities and interruption states.
- Do not promise unrestricted background recording.
- Validate hardware behaviour on physical devices.

### FR-11 Privacy and accessibility
- Recording begins only after explicit action and remains visibly indicated.
- Raw audio is not persisted by default.
- Logs do not contain raw audio, secrets or full transcript content by default.
- Caption size is adjustable; high contrast and screen-reader support are provided.

## Non-functional requirements
- Reliability: confirmed transcript entries survive app restart and supported reconnect flows.
- Performance: measure caption latency; do not claim unverified targets.
- Security: all data operations are user scoped.
- Maintainability: ASR provider is isolated behind an adapter.
- Portability: shared app code does not erase native platform differences.
- Observability: collect safe operational metadata only.

## Acceptance criteria
1. Specific recording works on supported physical Android and iOS devices.
2. Partial and final caption states are distinguishable.
3. Final transcript entries persist incrementally.
4. A day can contain multiple conversation threads.
5. VAD proposes boundaries; user can manually create, split, merge and rename.
6. Silence does not create empty conversations.
7. Day grouping follows stored local date and timezone.
8. User can edit, bookmark, search, export and delete.
9. Permission denial, OS interruption and network loss are communicated truthfully.
10. No raw audio is persisted in app storage, database, object storage or logs.
11. Each target language has provider capability and test evidence before being advertised as supported.
12. Accessibility is reviewed with assistive technology and target-user feedback.

## Open validation items
- Confirm provider streaming support for all six languages in the selected region.
- Evaluate Indian accents, noise and code-switching with consented representative samples.
- Confirm Android/iOS background behaviour by OS version and device.
- Obtain legal/privacy review of consent and disclosure wording.

# Inai — Coding Standards

## General
- Use small, reviewable changes and typed interfaces.
- Do not silently change approved product decisions or API contracts.
- Never claim a feature or test is complete unless it was run and verified.
- Handle loading, empty, offline, permission-denied and error states.

## React Native / TypeScript
- Enable strict TypeScript.
- Avoid `any`; type API payloads, native events and WebSocket messages.
- Keep domain logic out of presentational components.
- Keep native recording behind typed platform interfaces.
- Use accessible labels, roles and logical focus order.
- Never embed cloud secrets or provider credentials in the app.

## Kotlin / Android
- Follow current Android permission and foreground-service requirements.
- Keep capture lifecycle explicit and use bounded buffers.
- Handle permission revocation, audio focus, interruptions and route changes.
- Never write captured audio to disk under the current product policy.

## Swift / iOS
- Use explicit AVAudioSession lifecycle management.
- Handle interruptions, route changes and session reactivation.
- Do not assume background execution is unrestricted.
- Never persist raw audio under the current product policy.

## Python / FastAPI
- Use type hints and request/response schemas.
- Separate routes, domain services, repositories and provider adapters.
- Validate all input and derive user identity from trusted authentication.
- Use async-safe code in streaming paths and safe error responses.

## Database
- Use versioned migrations, UUIDs and `TIMESTAMPTZ`.
- Store day local date and timezone explicitly.
- Enforce user ownership and test cross-user access.
- Keep original transcript separate from translation.

## Testing and logging
- Unit-test state transitions and segmentation.
- Test APIs, migrations, WebSocket ordering/retries/duplicates.
- Test microphone lifecycle on physical Android and iOS devices.
- Never log raw audio, credentials, access tokens or full transcript text by default.
- Do not fabricate device, language or accuracy results.

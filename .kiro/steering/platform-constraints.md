# Inai — Platform Constraints

Aligned with the specification amendments A1–A14 approved on 2026-11-25. Items marked **[Unverified]** depend on the validation gate (T0.2).

## Cross-platform rule
Share UI and domain logic where practical. The native engine (Kotlin on Android, Swift on iOS) owns microphone capture, VAD, chunking, the replay buffer, streaming transport and background lifecycle, implemented separately per platform. Audio never reaches JavaScript, and the engine must keep working if JS is suspended.

## Android
- Follow the current target SDK's microphone permission and foreground-service requirements (microphone service type and matching permissions; notification permission for the persistent notification).
- Microphone is a while-in-use permission: start capture only from a visible, user-initiated state. After an interruption, resuming may require the user to act; expose this as a capability.
- Active capture is user initiated and visibly indicated.
- Use the required foreground service type and persistent notification where applicable.
- Handle permission revocation, microphone privacy toggle, audio focus, route changes, calls, process recreation and OEM battery restrictions.
- Exclude the local SQLite store from device backups.
- Test screen lock and background behaviour on physical devices and multiple OS versions.
- Do not promise uninterrupted all-day operation on every device.
- Android 15/16 specifics and Play foreground-service declarations are **[Unverified]**.

## iOS
- Provide an accurate microphone purpose string and request permission when needed.
- Use AVAudioSession and AVAudioEngine or a documented alternative.
- Handle interruptions, route changes, phone calls, other audio sessions and reactivation.
- Configure only background capabilities permitted for the actual use case and current App Store rules **[Unverified]**.
- Exclude the local SQLite store from device backups.
- Validate on physical iPhones; simulator tests are insufficient for audio lifecycle.
- If capture is suspended or terminated, mark the session interrupted, open a capture gap and preserve confirmed transcript data. Never imply capture continued.

## Shared requirements
- Expose platform capabilities to the UI, including whether automatic resume after interruption is possible.
- Keep buffers bounded and avoid raw audio disk persistence. The replay buffer is in memory only and its size is set by measurement.
- Represent reconnect gaps and interruptions explicitly as capture gaps. Network loss beyond the replay window and OS interruptions are gaps; user pauses are not.
- Signal interruptions, gaps and errors visually and with haptics, plus a local notification where the OS permits. Never rely on audio alerts.
- The local SQLite store is encrypted at rest with a key in Keychain/Keystore, never contains audio or tokens, and is wiped on sign-out and account deletion.
- Native token access for background streams (shared Firebase SDK session) is **[Unverified]**; the fallback is defined in the design.
- Document tested OS versions and device models.

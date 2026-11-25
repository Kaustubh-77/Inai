# Inai — Platform Constraints

## Cross-platform rule
Share UI and domain logic where practical. Implement microphone capture and background lifecycle separately for Android and iOS.

## Android
- Follow the current target SDK's microphone permission and foreground-service requirements.
- Active capture is user initiated and visibly indicated.
- Use the required foreground service type and persistent notification where applicable.
- Handle permission revocation, microphone privacy toggle, audio focus, route changes, calls, process recreation and OEM battery restrictions.
- Test screen lock and background behaviour on physical devices and multiple OS versions.
- Do not promise uninterrupted all-day operation on every device.

## iOS
- Provide an accurate microphone purpose string and request permission when needed.
- Use AVAudioSession and AVAudioEngine or a documented alternative.
- Handle interruptions, route changes, phone calls, other audio sessions and reactivation.
- Configure only background capabilities permitted for the actual use case and current App Store rules.
- Validate on physical iPhones; simulator tests are insufficient for audio lifecycle.
- If capture is suspended or terminated, mark the session interrupted and preserve confirmed transcript data. Never imply capture continued.

## Shared requirements
- Expose platform capabilities to the UI.
- Keep buffers bounded and avoid raw audio disk persistence.
- Represent reconnect gaps and interruptions explicitly.
- Document tested OS versions and device models.

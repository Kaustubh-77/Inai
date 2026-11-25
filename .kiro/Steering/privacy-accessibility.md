# Inai — Privacy and Accessibility

## Recording
- Start only after explicit user action.
- Explain microphone use before requesting permission.
- Show a clear, persistent recording state while capture is active.
- Provide obvious pause and stop controls.
- Never implement covert or silent recording.
- Explain that nearby people's speech may be transcribed; users should obtain appropriate consent and follow applicable rules. Obtain jurisdiction-specific legal/privacy review before launch.

## Retention
- Store transcript text and necessary metadata only.
- Raw audio may exist transiently in bounded memory while streaming.
- Do not save raw audio to local files, database blobs, object storage, analytics or logs.
- Keep original transcript separate from any future translation.
- Provide export and deletion controls and document backup deletion/retention.

## Security
- TLS in transit and managed encryption at rest.
- Keep ASR/cloud credentials on the server.
- Use least-privilege service identities.
- Enforce authenticated user ownership on every endpoint.
- Redact personal content from logs and crash reports.

## Accessibility
- Large adjustable captions and high-contrast option.
- Recording state must not rely on colour alone.
- Distinguish provisional from final captions.
- Meaningful screen-reader labels and logical focus order.
- Large, discoverable pause/stop controls.
- Support system font scaling and avoid clipped text.
- Test with deaf and hard-of-hearing participants; do not assume developer preferences represent user needs.

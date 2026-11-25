# Inai — Privacy and Accessibility

Items marked **[Approved Ax]** were approved by the owner on 2026-11-25 (A1–A14). Numeric accessibility targets are initial targets to validate with deaf and hard-of-hearing users.

## Recording
- Start only after explicit user action.
- Explain microphone use before requesting permission.
- Show a clear, persistent recording state while capture is active.
- Provide obvious pause and stop controls.
- Never implement covert or silent recording.
- Explain that nearby people's speech may be transcribed; users should obtain appropriate consent and follow applicable rules. Obtain jurisdiction-specific legal/privacy review before launch, including India's data protection law and consent rules for recording bystanders. Complete this review before real-user streaming is built (Milestone 5), not only at launch.

## Retention
- Store transcript text and necessary metadata only.
- Raw audio may exist transiently in bounded memory while streaming. This includes the native replay buffer, which is memory only.
- Do not save raw audio to local files, SQLite, database blobs, object storage, analytics or logs.
- Keep original transcript, user edits and any future translation as separate fields.
- Provide export and deletion controls and document backup deletion/retention. Backup retention period: to be set and documented before launch.
- Account deletion removes all server-side user data and the Firebase user, and wipes the local store.

## ASR provider data handling
- The ASR provider is a processor of raw audio. Inai storing no audio is not sufficient if the provider retains it.
- Before any real user audio is sent to a provider, verify and record its audio retention, logging, training/data-use policy, region and data residency, and how to opt out where applicable.
- Use consented test audio only until that verification is recorded. Sarvam AI is a candidate under evaluation; nothing is assumed about its policies.
- Disclose providers to users in the privacy notice.

## Consent and notices
- Record user acknowledgement of the privacy notice and recording-responsibility notice with version and time (`consent_records`).
- Re-prompt when notice versions change.

## Security
- TLS in transit and managed encryption at rest.
- Keep ASR, Firebase Admin and cloud credentials on the server.
- Authenticate with Firebase ID tokens verified server-side. Never put tokens in URLs or logs, including WebSocket URLs.
- Use least-privilege service identities.
- Enforce authenticated user ownership on every endpoint, with composite ownership constraints in the database.
- Redact personal content from logs and crash reports.
- Local store: encrypted at rest with a key held in Keychain/Keystore **[Approved A2]**; excluded from OS/cloud device backups; wiped on sign-out and account deletion **[Approved A12]**. Warn the user before sign-out if unsynchronised edits exist.
- Optional privacy-screen setting to hide transcript content in the app switcher **[Approved]**.
- Field-level encryption of transcript text on the server is an open decision (it limits server-side search).

## Accessibility
- Large adjustable captions and high-contrast option.
- Contrast: at least WCAG 2.2 AA (4.5:1 for text) in the standard theme; high-contrast mode targets 7:1.
- Recording state must not rely on colour alone.
- Distinguish provisional from final captions by more than colour (for example style plus a text label).
- Meaningful screen-reader labels and logical focus order.
- Screen-reader policy: never announce partial captions; announce finals through a polite live region, user-configurable.
- Large, discoverable pause/stop controls. Minimum 48 dp on Android and 44 pt on iOS, with pause/stop at least 56 dp/pt.
- Support system font scaling and caption size up to at least 200 percent without clipped text. Verify Tamil, Telugu, Kannada and Malayalam script line-height and shaping.
- Interruptions, capture gaps and errors are signalled visually (persistent banner) and with haptics, and by a local notification where the OS permits. Never rely on audio alerts.
- Localised app UI. Initial UI locales: to be decided.
- Test with deaf and hard-of-hearing participants; do not assume developer preferences represent user needs. Plan participant recruitment and informed consent for this research.

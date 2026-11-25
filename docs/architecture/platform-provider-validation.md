# Inai — T0.2 Platform and Provider Validation

Date checked: **2026-11-25**. Desk research only. No provider account, credential, audio or API call was used. No decision in this document changes an approved architecture decision. Sarvam AI is an evaluation candidate only; **no provider is selected**.

## How to read the evidence
- **[Official]** text seen in an excerpt from the vendor's or platform owner's own site.
- **[Official forum]** Apple Developer Forums post (community or staff answer; not a specification).
- **[Secondary]** blogs, Q&A sites, articles or competitor pages. Treat as leads.
- **[Vendor claim]** the vendor's own marketing or benchmark. Not independent.
- **[Unverified]** not found, or only inferred.
- **Limitation:** fetching the official pages from the sandbox failed with HTTP 403 for every documentation domain tried (Sarvam, Google Cloud, AWS, Microsoft, Android, Firebase). Findings come from search-result excerpts. A person with a browser must confirm the items listed under "Evidence still required" before any language is marked verified in the catalog.

---

## A. ASR provider capability matrix
Target languages: Tamil `ta`, Kannada `kn`, Malayalam `ml`, Telugu `te`, Hindi `hi`, English `en`.

### A1. Sarvam AI (first candidate; not selected)
| Question | Finding | Evidence |
|---|---|---|
| Real-time streaming over WebSocket | Yes. A "Realtime Streaming" WebSocket channel exists, powered by `saaras:v4` (default) or `saaras:v3-realtime` (legacy). | [Official] docs.sarvam.ai realtime WS reference |
| Partial transcripts | `saaras:v4` on the realtime plugin gives "true partial transcripts". | [Official] Sarvam LiveKit production guide |
| Final events | A "structured event and close-code protocol" exists. The exact final-event message shape was not seen. | [Official] same page; shape [Unverified] |
| Language coverage: all six | The WebSocket reference lists `hi-IN`, `kn-IN`, `ml-IN`, `ta-IN`, `te-IN`, `en-IN` among supported codes, and Saaras supports 22 Indic languages plus English. This was seen on the legacy/earlier WS page. The realtime page's own language table was not seen. | [Official excerpt] partially; realtime-specific support [Unverified] |
| Audio format | WS defaults to 16 kHz; only 16 kHz and 8 kHz are supported as a connection parameter (excerpt from the translate WS page). The separate Dictate API takes base64 16 kHz mono 16-bit, at most 1 s per message. Realtime STT framing, encoding and chunk size not confirmed. | [Official excerpt]; realtime format [Unverified] |
| Server-side VAD / endpointing | Realtime exposes millisecond VAD parameters (threshold, silence duration, minimum speech duration). This overlaps with the approved native VAD; the interaction needs a design note. | [Official excerpt] |
| Timestamps / segment offsets | Not seen for realtime. The "which API to use" page says features such as timestamps differ by API. | [Unverified] |
| Latency | No official figure seen. | [Unverified] |
| Accuracy evidence | Sarvam reports ~19% WER for Saaras V3 on its IndicVoices benchmark (~22% for the earlier model), and says V3 supports streaming. A press piece says its performance claims cannot yet be independently verified. No per-language Tamil/Malayalam/Kannada/Telugu figures seen. An arXiv paper compares Saaras v3 as a baseline; its numbers were not read. | [Vendor claim] sarvam.ai blog; [Secondary] Hindu BusinessLine; [Unverified] per language |
| Pricing | New verified users get ₹100 free credits. One competitor-hosted article says ₹30 per hour of STT billed per second, rounded up. Official STT price not seen. | [Official] credits; price [Secondary, Unverified] |
| Rate limits | An official "Credits & Rate Limits" page exists; limits are per account and shared with Speech-to-Text. Numbers not seen. | [Official excerpt]; values [Unverified] |
| Session duration and idle limits | Not seen for realtime. (The Dictate API ends a turn after ~18–20 s of continuous speech with VAD endpointing, which is a different product.) | [Unverified] |
| Regional availability / residency | Sarvam says inference runs in India for one product line (Indus); its Trust Center says it does not move data across borders unless asked and does not share data across tenants. Whether STT inference is India-only is not stated in what I saw. | [Official excerpt]; STT specifics [Unverified] |
| Audio retention and deletion (STT) | Not found for STT. The only retention statement seen is for Document AI (45 days default; enterprise policy zero retention to one year), which does not apply to speech. Sarvam's public privacy policy excludes content processed for enterprise customers (governed by customer agreements). | [Official]; STT policy [Unverified] |
| Use of customer audio for training | Not found. Trust Center says custom models trained on a customer's data stay in the customer's environment. No statement about default STT audio use. | [Unverified] |
| Security and privacy controls | Trust Center page exists. Certifications, encryption and access controls not read. | [Unverified] |

**Blocking gap:** STT audio retention, logging and training policy is unknown for Sarvam. Per the approved privacy rule, no real audio can go to Sarvam until this is confirmed in writing.

### A2. Alternatives with meaningful official evidence
| Provider | Streaming and languages | Retention and training | Gaps |
|---|---|---|---|
| **Google Cloud Speech-to-Text V2 (Chirp 3)** | Chirp 3 supports `StreamingRecognize` and is V2-only. GA regions seen: `us` and `eu` multi-regions; a public-preview launch in `asia-south1` (and others) appears in the release notes. [Official] Per-language streaming support not seen; Google says to query the locations API for current languages. Streaming request audio is limited to 25 KB per message (V1 doc excerpt). [Official] | By default Google does not log customer audio or transcripts; data logging is an opt-in program. [Official] | Which of `ta`, `kn`, `ml`, `te`, `hi`, `en` stream with Chirp 3; whether `asia-south1` supports streaming for them; stream duration limit; price. |
| **Amazon Transcribe** | Streaming is not available for all languages; the "Data input" column of the supported-languages table shows it. [Official] A 2023 re:Post answer says Telugu was batch-only then. [Secondary, dated] `hi-IN` appears in a Chime SDK streaming list. [Official] | Content may be used to develop and improve the service by default; customers can opt out through an AWS Organizations AI services opt-out policy. [Official] | Streaming status for `ta`, `kn`, `ml`, `te` today; Indian-region availability. |
| **Azure AI Speech** | A Sept 2026 announcement lists Tamil, Telugu, Kannada and Malayalam as new languages for the Speech LLM. [Official] Whether this applies to real-time streaming, and which locales, was not confirmed. MAI-Transcribe-2-Streaming is a low-latency streaming model covering 60 languages. [Official] | Microsoft states real-time speech-to-text does not retain or store customer data (Q&A, 2023). [Official Q&A] Audio and transcription logging is optional; logs kept 30 days. [Official] | Indic streaming locales and regions (e.g. India) and quotas. |
| **ElevenLabs Scribe v3 Live** | Claims 150 ms latency and 90+ languages. [Vendor claim] Indic languages not itemised in what I saw. | Not seen. | Everything per language. |
| **Soniox** | Pages for Tamil and Telugu state real-time WebSocket transcription. [Vendor claim] Kannada and Malayalam pages not seen. | Not seen. | Everything per language. |

### A3. Comparison summary
Official evidence supports a meaningful comparison **only on data handling**: Google (no logging by default), Microsoft (real-time not stored), AWS (used for improvement unless you opt out), Sarvam (STT policy unknown). On the six-language streaming question, no provider can be marked verified from the evidence I could read. All per-language rows stay `unverified` in the language catalog.

### A4. Evidence still required (needs a browser or the provider)
1. Sarvam realtime page: language table, audio format and framing, event schema, session/idle limits, rate limits, STT price.
2. Sarvam written statement on STT audio retention, logging and training, and data residency (contract or DPA terms).
3. Google: supported-languages table filtered to Chirp 3 + streaming, and the locations API result for the intended region.
4. AWS: "Data input" column for `ta`, `kn`, `ml`, `te`, `hi`, `en`.
5. Azure: real-time locale list for `ta-IN`, `te-IN`, `kn-IN`, `ml-IN`, `hi-IN`, `en-IN` and India regional availability.
6. For every candidate: whether results include timestamps or offsets.
7. Measured quality and latency on consented samples. **Not started.** No audio may be used until you provide and approve it.

---

## B. Android and iOS platform validation

### B1. Android
| Topic | Verified facts | Evidence |
|---|---|---|
| Foreground service type | From Android 14 (API 34) an app must declare a foreground service type in the manifest and request the matching FOREGROUND_SERVICE_* permission; some types also need a runtime permission. Missing type raises `MissingForegroundServiceTypeException`. | [Official] developer.android.com FGS types |
| Microphone service | Needs a microphone type plus `RECORD_AUDIO`; the exact manifest text for microphone was seen only in secondary summaries. | [Secondary]; confirm on the official page |
| Start from background | A foreground service that needs while-in-use permissions (including microphone) cannot be created while the app is in the background, even for exempt cases. A service started from the background cannot access the microphone. | [Official] Android 11 and Android 12 FGS pages |
| Long-running limits | Android 15 timeouts apply to `dataSync` (6 hours per 24 h) and `mediaProcessing`. A microphone timeout was not mentioned in the excerpts; absence is **not confirmed**. Android 16 changes not verified. | [Official] Android 15 behaviour changes; microphone/16 [Unverified] |
| Doze and standby | Doze defers background CPU and network for idle devices; App Standby defers background network for unused apps. | [Official] |
| OEM restrictions | Community data shows OEM-specific kills; one entry says Samsung (Android 11) stopped apps holding wake locks in foreground services. | [Secondary] dontkillmyapp.com |
| Play policy | Foreground service types must be declared and appropriate; declarations are reviewed in Play Console. A newer "preview" policy page on FGS and full-screen intents exists. | [Official] Play Console help; details [Unverified] |
| Notifications | `POST_NOTIFICATIONS` is a runtime permission on Android 13+ for the persistent notification (general platform knowledge). | [Unverified] this session |
| Backup | Auto Backup excludes `getNoBackupFilesDir()`, cache and code-cache directories. From Android 12, `dataExtractionRules` governs cloud backup and transfers; `allowBackup`/`fullBackupContent` apply before. | [Official] Auto Backup guide; rules [Secondary] |

**Technically possible:** user-initiated foreground microphone capture that continues with screen off, with a visible notification.
**Needs physical-device testing:** survival over hours, behaviour on Samsung/Xiaomi/Oppo/OnePlus-class devices, Doze and Battery Saver interactions, call interruptions, route changes, process death, Android 15 and 16 behaviour, battery and data cost over a full day.
**Not possible:** restarting microphone capture from the background after an interruption without user action (confirmed by the while-in-use rule).

### B2. iOS
| Topic | Verified facts | Evidence |
|---|---|---|
| Start in foreground only | An app must be in the foreground to start recording. With the `audio` background mode it can keep recording after moving to the background. If recording stops, the system suspends the app. | [Official forum] Apple Developer Forums |
| Cannot start from background | Apple restricts starting an `AVAudioSession` recording from a fully backgrounded state. | [Official forum] |
| Interruptions | An interruption may suspend the app (e.g. accepted call). An "interruption ended" notification is **not guaranteed**; the app must decide whether to reactivate its session on return to the foreground. | [Official] Audio Session Programming Guide (archive) |
| Route changes | When a headset is unplugged during recording, the system sends a route-change notification with a reason and the previous route; the guidance is that recording should stop. | [Official] same guide (archive) |
| Restart after interruption | Developers report engine/session failing to restart after a call, in background. | [Official forum] |
| **New risk** | A May 2026 forum report says iOS 26.5 terminated an audio-recording app with SIGKILL after ~50 s of background time even with `UIBackgroundModes` audio, with no interruption notification. It is one unconfirmed developer report. | [Official forum, single report] |
| App Review | Background modes may only be used for their intended purposes; apps are rejected when the declared mode has no reviewable feature. Microphone access needs a clear purpose string. An app privacy label is required. | [Official forum] 2.5.4-related; [Official] 5.1.1 and privacy details pages |
| Indicator | iOS shows a microphone indicator while recording (general platform behaviour). | [Unverified] this session |
| Backup exclusion | `isExcludedFromBackup` for local files (general knowledge). | [Unverified] this session |

**Technically possible (per sources):** user-started foreground capture with `audio` background mode continuing in the background.
**Needs physical-device testing:** the iOS 26.5 background-kill report on current iOS versions, overnight/long runs, interruption and reactivation behaviour, route changes (Bluetooth, wired), battery.
**Not possible:** starting capture from the background or from automation.
**App Review risk:** the `audio` background mode must be justified as user-initiated transcription capture; review outcome cannot be predicted.

---

## C. Firebase authentication validation
| Question | Finding | Evidence |
|---|---|---|
| ID token lifetime and refresh | ID tokens last one hour. A long-lived refresh token gets new ID tokens; client SDKs refresh transparently. | [Official] Firebase manage-sessions page and Admin reference |
| SDK availability | React Native Firebase wraps the native Android and iOS Firebase SDKs directly. Native Kotlin and Swift SDKs are the underlying libraries. | [Official] rnfirebase.io |
| Native access to the same session | Because the RN package wraps the native SDKs, a native module in the same app process should see the same signed-in user and be able to request an ID token. Not confirmed in docs. | **[Unverified inference]** |
| Background token refresh | Not documented in what I saw. Developers report confusion about automatic refresh timing in React Native. | [Secondary] Stack Overflow; behaviour **[Unverified]** |
| Server verification | The Admin SDK needs a service account to verify ID tokens. Python verification checks the issuer prefix `https://securetoken.google.com/`. A `clock_skew_seconds` option exists, limited to 0–60 s after a "Token used too early" issue. | [Official]; [Official source code on GitHub]; PR/issue |
| Revocation | The Admin SDK can revoke refresh tokens and check ID-token revocation; an ID token stays valid until expiry unless the check is performed. | [Official excerpt] manage-sessions |
| First-message WebSocket auth and in-band re-auth | No Firebase-specific constraint found. Token in the first message avoids URL leakage; re-auth at under one hour is feasible because the ID token itself expires at one hour. | design reasoning; **[Unverified]** end to end |
| Secure handling in native engine | Keep the token in memory only; request a fresh token from the Firebase SDK before expiry; never persist or log it. | recommendation |
| Sign-in method cost | Phone/SMS needs the Blaze plan and is billed per SMS; email/social are free to a large MAU limit. | [Secondary] |

**Conclusion:** the approved architecture is consistent with the evidence. The one open risk is whether the native engine can obtain a fresh token while the app is backgrounded for hours. Test on physical devices in M4. The approved fallback (JS pushes tokens, stream ends as an `auth_expired` gap) already covers failure. **No change proposed.**

---

## D. SQLite options (no library selected, nothing installed)
| Option | Encryption | FTS / search | Sync fit | Notes | Evidence |
|---|---|---|---|---|---|
| **op-sqlite** (op-engineering) | SQLCipher supported | FTS5 listed as a plugin | Plain SQLite; our own sync layer fits | JSI-based; New Architecture compatibility to confirm | [Official] package/docs excerpts |
| **expo-sqlite** | SQLCipher support referenced through a config plugin; details unclear | FTS5 depends on build flags | Plain SQLite | Needs Expo config-plugin/CNG workflow; fit with bare React Native to confirm | [Official] Expo docs; [Secondary] issue |
| **react-native-sqlite-storage** and SQLCipher forks | SQLCipher via forks | Depends on build | Plain SQLite | Older bridge-style libraries; maintenance and New Architecture status to confirm | [Secondary] GitHub |
| **PowerSync** (SQLite sync SDK) | SQLCipher option | n/a | **Imposes its own sync service** | Does not match the approved custom sync design; not recommended without a decision | [Official] |
| Native SQLite per platform (SQLCipher, GRDB) | SQLCipher | Platform-specific | Own | Not required: the native engine stores no transcripts | design |

Cross-cutting findings:
- **Keychain/Keystore integration:** SQLite libraries encrypt with a supplied key; storing that key in Keychain/Keystore needs a separate secure-storage component. Not verified for any option. **[Unverified]**
- **Backup exclusion:** Android Auto Backup skips `getNoBackupFilesDir()`, and `dataExtractionRules` can exclude the database domain [Official/Secondary]. The library must let the app choose the database path. iOS exclusion flag is general knowledge, not verified here.
- **Indic search:** SQLite's FTS5 `trigram` tokenizer has shipped since 3.34 (Dec 2020) and supports substring matching without word segmentation. [Secondary + project README] The default `unicode61` tokenizer reportedly drops many substrings in unsegmented scripts (Japanese example). [Secondary] For Indic scripts, whether `unicode61` splits words at combining vowel signs is **[Unverified]** and must be tested in the search spike (T1.1). Trigram queries shorter than three characters need a `LIKE` fallback **[Unverified]**.
- **FTS5 availability:** FTS5 must be compiled in (`SQLITE_ENABLE_FTS5`). [Secondary] Confirm per library.
- **Unicode normalisation:** SQLite does not normalise Unicode by itself; normalise to NFC in app code with shared test vectors (matches the approved design).
- **Offline editing and sync:** all options store rows; the approved queue, compare-and-set and cursor sync are application-level, so any plain SQLite option fits.
- **Shortlist for the spike (not a selection):** op-sqlite with SQLCipher, expo-sqlite with SQLCipher, one legacy library as a baseline.

---

## E. Sources (checked 2026-11-25)
**Sarvam:** docs.sarvam.ai realtime streaming guide and WS reference (api-reference/speech-to-text/transcribe/realtime/ws; api/api-guides-tutorials/speech-to-text/realtime-streaming); WS legacy reference (api-reference-docs/speech-to-text/transcribe/ws); LiveKit production guide (api/integration/livekit-production-best-practices); which-api-to-use page; pricing and rate-limits page (api/getting-started/pricing); Dictate limits page; Doc AI data-retention page (doc-ai/resources/data-retention); sarvam.ai/privacy-policy; sarvam.ai/trust-center; sarvam.ai/blogs/asr; smallest.ai/blog/sarvam-ai-speech-to-text-pricing [Secondary]; thehindubusinessline.com article on performance claims [Secondary].
**Google Cloud:** docs.cloud.google.com/speech-to-text/docs/models/chirp-3; /speech-to-text-supported-languages; /release-notes; /v1/data-logging; /v1/data-usage-faq; /streaming-recognize.
**AWS:** docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html; /streaming.html; /opt-out.html; repost.aws Telugu question [Secondary, 2023]; Chime SDK EngineTranscribeSettings page.
**Microsoft:** learn.microsoft.com Azure Speech language-support page; devblogs.microsoft.com/foundry/announcing-azure-ai-speech-llm-09-2026; MAI-Transcribe-2-Streaming page; Microsoft Q&A "Data storage when using Azure Speech"; logging-audio-transcription page.
**Others:** elevenlabs.io/realtime-speech-to-text; soniox.com/speech-to-text/tamil and /telugu (vendor claims).
**Android:** developer.android.com FGS service types, declare, Android 11 FGS privacy, Android 12 FGS restrictions, Android 14 FGS types required, Android 15 behaviour changes and FGS type changes, Doze/standby, Auto Backup; support.google.com Play Console foreground-service pages; dontkillmyapp.com [Secondary].
**Apple:** developer.apple.com Audio Session Programming Guide (archive: interruptions, route changes, activating a session); developer.apple.com App Review 5.1.1 purpose strings and App Privacy Details; Apple Developer Forums threads 770556, 815725, 826462, 106415, 79849, 760896.
**Firebase:** firebase.google.com/docs/auth/admin/manage-sessions; /admin/verify-id-tokens; Admin Python reference; github.com/firebase/firebase-admin-python (`_token_gen.py`, PR 714, issue 624); rnfirebase.io; supertokens.com and blog.logto.io pricing [Secondary].
**SQLite and React Native:** npmjs.com/package/@op-engineering/op-sqlite; docs.expo.dev SQLite; powersync docs; sqlite.org/fts5.html; github.com/simonw/sqlite-fts5-trigram; reactnative.dev blog 0.87 and 0.84; react-native.dev compatibility matrix.

## F. Verified facts, assumptions, recommendations and open questions
**Verified (from official excerpts):** Sarvam realtime WS exists with partial transcripts and VAD parameters; Chirp 3 streams via V2 and Google does not log by default; AWS streaming is not universal and content is used for improvement unless opted out; Azure real-time is described as not stored; Firebase ID tokens last one hour; Android FGS type and while-in-use rules; iOS foreground start and audio background mode behaviour; RN 0.87 minimums.
**Assumptions (unverified):** Sarvam realtime supports all six languages with usable quality; native engine can refresh Firebase tokens in the background; Android microphone FGS has no timeout; SQLite FTS tokenizers handle Indic combining marks; Swift on Linux cannot build iOS apps.
**Recommendations (for your review, no change to approved decisions):**
1. Treat the provider spike as blocked on three inputs: written STT retention/training terms, consented audio, and the manual document reads in A4.
2. Add the iOS background-kill report (B2) as an explicit physical-device test case in T4.3.
3. Keep the language catalog fully `unverified` until evidence exists; the app then cannot start recording, which is the intended safe default.
4. Shortlist SQLite options for T3.4 as in D; run the search spike (T1.1) before choosing tokenizers.
5. Decide sign-in methods early because phone sign-in implies Blaze billing and SMS cost.
**Open questions:** cloud vendor, region, hosting; sign-in methods; UI locales; final ASR provider; iOS build and device ownership; macOS CI runner; SQLite library and encryption; PostgreSQL version and hosting; server-side transcript encryption and row-level security; backup retention.

**Note on concurrency:** the one-active-stream policy is no longer an open question. It is defined by approved decision A11 (rejection of a second stream, resume, pause, expiry and recovery). Implementation must validate the approved A11 concurrency and lifecycle rules through the T2.6 tests.

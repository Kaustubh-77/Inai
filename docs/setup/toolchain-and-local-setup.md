# Inai — T0.1 Toolchain Inspection and Local Setup Guide

Inspected: 2026-11-25. Inspection only. Nothing was installed, configured or modified.
Evidence labels: **[Inspected]** observed in the sandbox this session. **[Official]** seen in an official excerpt. **[Secondary]** third-party source. **[Unverified]** not confirmed; check before relying on it.
Note: fetching official documentation pages from the sandbox returned HTTP 403, so documentation findings come from search excerpts. Confirm exact versions on the official pages before pinning.

**How to read this document.** Sections 1, 2 and 7 are a **historical snapshot** of a Linux sandbox on 2026-11-25. They are not the current state of any developer machine or of CI, and they do not record project decisions. The "Current project decisions" section below supersedes the snapshot wherever they differ (for example Python, PostgreSQL and CI). Items in sections 3 to 6 that are still marked open or **[Unverified]** remain open.

## 0. Current project decisions (updated 2026-11-26, after T0.4)
| Area | Current state | Source |
|---|---|---|
| Python | 3.11 (`requires-python = ">=3.11,<3.12"`) | `backend/pyproject.toml` |
| Dependency management | uv. Versions are pinned by the committed `backend/uv.lock`; install with `uv sync --locked`. | `backend/README.md` |
| Backend stack (M1) | FastAPI, Uvicorn, SQLAlchemy 2, Alembic, firebase-admin, psycopg 3 (`psycopg[binary]>=3.2,<4`), pytest, Ruff, mypy (strict) | `backend/pyproject.toml`, `backend/uv.lock` |
| PostgreSQL for M1 development and CI | **PostgreSQL 16.** The manual `t04-lock-and-verify` workflow starts a `postgres:16` service container and verifies connectivity and the server major version. | `.github/workflows/t04-lock-and-verify.yml` |
| PostgreSQL elsewhere | The draft DDL needs PostgreSQL 15 or later. The version for a managed production database depends on the still-open cloud decision. | `design.md` §14 |
| CI | GitHub Actions. `backend-ci` runs the locked install, Ruff, mypy and pytest. iOS runner availability and the device-test approach are still open (section 6). | `.github/workflows/` |
| Firebase, cloud vendor, ASR provider | Unchanged. See sections 5 and 6 and the steering files. No provider is selected. | `.kiro/steering/` |

Machine-specific note, inspected 2026-11-26 on the Windows development machine: no local `psql` and no local `uv` were found. This is a property of that machine, not a project decision. PostgreSQL-dependent checks currently run in GitHub Actions.

## 1. Sandbox inventory (historical snapshot, 2026-11-25) [Inspected]
| Item | Result |
|---|---|
| OS / hardware | Amazon Linux 2023, x86_64, 8 CPUs, 30 GB RAM, 88 GB free disk |
| Node / npm | v22.23.4 / 11.4.2; corepack 0.36.0 (provides yarn and pnpm shims) |
| Python | 3.11.15, pip 26.2.2, uv 0.13.5. `fastapi` not installed. Poetry, pipx missing |
| Java | OpenJDK 25.0.5.1 (`JAVA_HOME` unset). Maven 3.9.16 present |
| Gradle, Kotlin (`kotlinc`) | Missing |
| Android SDK, `sdkmanager`, `adb`, emulator | Missing; `ANDROID_HOME` unset |
| Xcode, `xcrun`, CocoaPods | Missing (cannot exist on Linux) |
| Swift | 6.3 (Linux toolchain). Cannot build iOS apps; iOS SDKs (UIKit, AVFoundation) are macOS-only [general knowledge, Unverified here] |
| Ruby / Bundler | 3.4.10 / 2.6.9 |
| PostgreSQL (`psql`, `postgres`, `pg_ctl`) | Missing |
| Docker | `docker` command is a Podman shim; it fails ("could not find a working conmon binary"). Containers are not usable now |
| Watchman | Missing |
| git / gh | 2.50.1 / 2.95.0 (authenticated to GitHub through the gateway) |
| Firebase CLI, gcloud, Azure CLI, Terraform | Missing. AWS CLI 2.36.47 present (no credentials configured or used) |

## 2. What the sandbox could and could not do (historical snapshot)
**Could (after owner-approved installs):** TypeScript domain logic and unit tests, Python/FastAPI backend, migrations and API tests (needs a PostgreSQL instance), WebSocket protocol tests with a fake ASR provider, Kotlin and Android Gradle builds (needs JDK/Gradle/Android SDK installs, ~several GB).
**Could not:** build or run iOS (no Xcode), run any physical-device audio test, run an Android emulator with microphone behaviour that proves lifecycle rules (no devices; emulator also absent).
**Restrictions found in that sandbox:** Docker was non-functional, so a containerised PostgreSQL was not available there without fixing the container runtime or installing PostgreSQL natively. Doc sites blocked `web_fetch` (HTTP 403). PostgreSQL 16 for the project is provided by the GitHub Actions service container (section 0).

## 3. Required tools and recommended versions
| Area | Requirement | Evidence |
|---|---|---|
| React Native | Latest stable at check time: 0.87 (Aug 2026). Raises minimums to Node.js 22, Android Gradle Plugin 9, Kotlin 2.0+. Strict TypeScript API is the default. | [Official] reactnative.dev blog 2026-08-11 |
| Node.js | 22.13 or newer | [Official excerpt] react-native.dev compatibility matrix |
| New Architecture | Legacy architecture is being removed (RN 0.82 removed the opt-out) | [Secondary] reactnative.com |
| JDK | JDK 17 is the long-standing RN requirement; whether RN 0.87 / AGP 9 needs a newer JDK is **[Unverified]**. The sandbox has JDK 25, which is likely too new for Gradle/AGP until confirmed | check RN 0.87 docs |
| Android Studio / SDK | Current Android Studio; Android SDK Platform and Build-Tools versions per RN 0.87 template and Play target API requirement **[Unverified]**; `ANDROID_HOME` and `JAVA_HOME` set | [Official] RN environment guide lists Node, Watchman, CLI, JDK, Android Studio |
| Kotlin / Gradle | Kotlin 2.0+ (RN 0.87 minimum); Gradle version per AGP 9 **[Unverified]** | [Official] RN blog |
| iOS | macOS with a current Xcode; exact minimum Xcode and macOS for RN 0.87 **[Unverified]**; Swift (Xcode-bundled), CocoaPods or experimental SwiftPM | [Official] RN blog mentions experimental SwiftPM |
| Python | **Decided for M1: 3.11**, pinned in `backend/pyproject.toml` (section 0). | `pyproject.toml` |
| FastAPI stack | **Approved M1 stack, installed through the committed lock** (section 0): FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, `firebase-admin`, psycopg 3, pytest. A WebSocket library for T2.1 is not yet chosen. | `pyproject.toml`, `uv.lock` |
| PostgreSQL | **16 for M1 development and CI** (section 0). The draft DDL needs 15 or later. The version for a managed production database depends on the open cloud decision. | workflow, `design.md` §14 |
| Firebase | See section 5 | |
| Watchman | Recommended by the RN setup guide for macOS/Linux development | [Official] |

## 4. Local setup guide (not executed; for a developer machine)
### 4.1 Common (macOS or Linux)
1. Install Git and GitHub CLI; clone `Kaustubh-77/Inai`.
2. Install Node 22.13+ (nvm or fnm); enable corepack; pick one package manager and record it in the repo (not decided).
3. Install Python 3.11 and `uv`; from `backend/` run `uv sync --locked` to create the virtual environment from the committed `uv.lock`.
4. Provide PostgreSQL 16 for local database work (the version used in CI) and create a local database and role (no shared credentials). Until a local instance exists, PostgreSQL-dependent checks run in GitHub Actions.
5. Install Firebase CLI if using the Authentication emulator (needs Node and a compatible Java; Java 25 compatibility is **[Unverified]**).

### 4.2 Android (macOS, Windows or Linux)
1. Install a JDK version confirmed for RN 0.87 / AGP 9, Android Studio, the required SDK platform, build-tools and command-line tools.
2. Set `ANDROID_HOME` and `JAVA_HOME`; accept SDK licences.
3. Use a physical Android device (USB debugging) for all microphone lifecycle tests. Emulators are insufficient for lifecycle claims.

### 4.3 iOS (macOS only)
1. macOS version required by the chosen Xcode; install Xcode and command-line tools; accept the licence.
2. Install CocoaPods (or SwiftPM when the project adopts it) and Watchman.
3. Apple Developer Program membership is needed for device signing and distribution.
4. Use physical iPhones for all audio lifecycle tests.

### 4.4 Backend
See `backend/README.md` for setup, quality checks and the dependency-lock update process. Database migrations (T1.2) are not implemented yet. Firebase token verification is tested with the Authentication emulator or test doubles. No real credentials are used in tests.

## 5. Firebase Authentication prerequisites
- A Firebase project owned by the user (not created in this task). Creating it is an owner action.
- Android and iOS app registrations with `google-services.json` and `GoogleService-Info.plist` (kept out of git unless the owner decides otherwise).
- A service account for the Admin SDK on the backend; the Admin SDK needs one to verify ID tokens [Official, firebase.google.com verify-id-tokens]. Stored in a secrets manager, never in the repo.
- Sign-in methods are an open decision. **Phone (SMS) sign-in needs the pay-as-you-go Blaze plan and is billed per SMS** [Secondary: Logto, SuperTokens; a Firebase notice quoted on Google Groups says SMS is not supported on Spark]. Email and social sign-in are listed as free up to 50,000 MAU [Secondary].

## 6. CI/CD requirements
- The repository is on GitHub and **GitHub Actions is in use** for the backend (`backend-ci` and the manual `t04-lock-and-verify`). Mobile, native and iOS CI are not set up yet.
- Linux runners can run lint, type checks, Python tests, PostgreSQL service tests and Android builds.
- **iOS builds and tests need macOS runners** (GitHub-hosted macOS or self-hosted Mac). Availability and cost are open decisions (D5).
- Physical-device tests cannot run on hosted CI. A device farm or manual device matrix is required **[open decision]**.
- Secrets for signing, Firebase and any provider must be CI secrets; none exist yet.

## 7. Missing tools and limitations summary (historical snapshot, 2026-11-25)
In that Linux sandbox the following were missing: PostgreSQL, a working container runtime, Gradle, Kotlin compiler, Android SDK/adb, Xcode, CocoaPods, Watchman, Firebase CLI, FastAPI and any project dependencies. Environment limits: no iOS, no devices, restricted doc fetch. The backend dependencies and PostgreSQL 16 are since covered by the committed lock and GitHub Actions (section 0). The owner still has to resolve the remaining items (installs, macOS access, devices) before M3 mobile builds and M4 native work, and before any local PostgreSQL use.

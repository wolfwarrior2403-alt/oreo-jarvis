# Oreo — Personal AI Assistant

Oreo is a voice-first, context-aware AI assistant: a FastAPI backend
(speech-to-text, emotion detection, a vector-store-backed memory, a
LangChain+Ollama reasoning agent, and TTS) paired with a mobile client.
Every action that changes something in the world — sending something,
writing a file, creating a calendar event — is gated behind an explicit
confirmation step before it runs.

Full original design doc: [ARCHITECTURE.md](ARCHITECTURE.md).

**One deviation from that doc:** section 4.1 suggests Kivy/Flutter for the
mobile client; this repo uses **React Native** instead, for the same
"one codebase, both platforms" goal. Everything else — the 4 screens, the
confirmation-gate UX, wake-word integration point, background-service
behavior — follows the doc as written.

## Repository layout

```
Oreo_jarvis/
  ARCHITECTURE.md     # the original design doc, verbatim
  backend/            # FastAPI gateway — see backend/README.md
  mobile/             # React Native client (Android/iOS) — see mobile/README.md
```

## Quick start

**Backend** (see [backend/README.md](backend/README.md) for full detail):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in JWT_SECRET_KEY, DATA_ENCRYPTION_KEY, DEVICE_PAIRING_CODE
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Mobile** (see [mobile/README.md](mobile/README.md) for full detail):
```bash
cd mobile
npm install
# point Settings at your backend's URL + the DEVICE_PAIRING_CODE from above
npm run android   # or npm run ios — see mobile/README.md re: native project setup
```

## What's fully functional today

- Backend API surface (all 6 endpoints from architecture doc section 3.1),
  JWT auth with device pairing + refresh token rotation.
- The **confirmation gate** end-to-end: the reasoning agent can only
  *propose* non-read-only actions; they sit in a `pending_actions` table
  until `POST /execute/action` is called with explicit approval, and every
  execution is logged with a timestamp (`action_logs` table +
  `oreo.audit` structured logger). This is covered by the backend test
  suite specifically because it's the hard safety requirement in the doc.
- STT (Faster-Whisper), prosody extraction (librosa), a rule-based emotion
  classifier, a Chroma vector store + SQLAlchemy profile DB, a
  LangChain+Ollama tool-calling agent, TTS (pyttsx3/Piper), AES-256-GCM
  encryption at rest for transcripts, and a `/train/upload` pipeline that
  chunks/embeds/indexes text documents.
- 17 backend pytest tests, all passing, with every heavy model call
  mocked — no GPU, no multi-GB downloads, no network access required to
  run them.
- A real, structured React Native app: all 4 required screens (Home,
  Confirmation, History, Settings), a JWT-authenticated API client with
  automatic token refresh, and a device-pairing flow.

## What needs real infrastructure/credentials to finish

These are documented as such in code comments and the relevant README —
nothing here silently pretends to work when it doesn't:

- **Wake-word detection ("Oreo").** Needs a free Picovoice AccessKey and a
  custom-trained "Oreo" `.ppn` model file (Porcupine's free built-in words
  don't include "Oreo"). See `mobile/src/services/wakeword.ts`.
- **Native Android/iOS projects.** `mobile/android/` and `mobile/ios/`
  ship the app-specific native additions (a foreground-service stub +
  NativeModule bridge for Android, a written explanation for iOS) but not
  a full generated Gradle/Xcode project — that's a one-time `npx
  @react-native-community/cli init` step. See `mobile/android/README.md`.
- **Real microphone capture.** The Home screen's capture button currently
  round-trips a placeholder audio file to exercise the full API path;
  wiring an actual recorder library is a follow-up.
- **Android background/locked-screen listening.** The foreground service
  shell exists; running Porcupine natively inside it (rather than in JS,
  which only runs while the app is foregrounded) is a marked TODO.
- **iOS background/locked-screen listening.** Not achievable the way
  Android's foreground service is — this is an Apple OS policy limit, not
  a bug here. Full explanation in `mobile/ios/OreoWakeWordNotes/README.md`.
- **Production-size Whisper model.** Defaults to a small model so local
  dev doesn't require a multi-GB download; swap `WHISPER_MODEL_SIZE` to
  `large-v3-turbo` (per the doc) once you have the hardware.
- **A trained emotion classifier.** Currently rule-based (prosody +
  keyword lexicon) — good enough to be genuinely useful, but the doc's
  intent of a proper trained classifier is a documented future step.
- **LoRA fine-tuning pipeline (section 5, "Training Pipeline" step 3).**
  Upload → embed → index works today; the fine-tune-and-redeploy step is a
  stub (`queue_lora_finetune` in `backend/app/routers/train.py`) since it
  needs GPU training infrastructure this environment doesn't have.
- **Local LLM.** The reasoning agent needs a running Ollama instance
  (`ollama pull llama3.2`) to actually converse; without one, `/voice/
  process` degrades to a clear "couldn't reach my reasoning model"
  response instead of crashing.

## Security posture (architecture doc section 6)

- JWT auth, short-lived access tokens + rotating refresh tokens, scoped to
  a paired device.
- AES-256-GCM encryption at rest for transcripts (`backend/app/crypto.py`;
  see that file and `backend/README.md`'s "Key management" section for how
  the key is handled).
- **Action gating is enforced, not just documented**: no non-read-only
  tool executor is ever called except from `execute_action()`, and only
  once a `PendingAction` row has status `approved`. Every execution — pass
  or fail — writes a timestamped `ActionLog` row.
- Data minimization: raw audio is deleted right after transcription unless
  `RETAIN_RAW_AUDIO=true` is explicitly set.
- Local-first default: nothing leaves the backend's own host unless you
  choose Deployment Option B/C and configure it that way yourself.

Deploying publicly (Option B)? Put the backend behind a real TLS
terminator and lock down CORS in `backend/app/main.py` (it's wide open by
default for local/LAN dev convenience) before exposing it to the internet.

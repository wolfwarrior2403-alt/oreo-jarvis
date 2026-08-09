# Oreo Mobile (React Native)

Cross-platform (Android/iOS) client for the Oreo backend — section 4 of the
architecture doc. Implements the 4 screens (Home/Listening, Confirmation,
History, Settings), a JWT-authenticated API client, and integration points
for Porcupine wake-word detection and an Android foreground service for
always-listening behavior.

## What's real vs. what's a stub — read this first

**Fully implemented (JS/TS layer, runs in Metro/a simulator today):**
- All 4 screens + a Pairing screen, wired through React Navigation.
- API client (`src/api/`) with JWT storage (`react-native-keychain` for
  tokens, `AsyncStorage` for plain settings) and automatic access-token
  refresh on 401.
- The confirmation-gate UX: `ConfirmationScreen` calls `POST
  /execute/action` and nothing executes without an explicit Approve tap.
- Settings: backend URL, wake-word sensitivity, Porcupine key, data
  retention toggle.

**Stubbed / needs real infra to finish (documented, not faked):**
- **Native Android/iOS projects.** `mobile/android/` and `mobile/ios/` do
  NOT contain full generated Xcode/Gradle projects — see
  `mobile/android/README.md`. Run `npx @react-native-community/cli init`
  once to generate them, then merge in this repo's `android/app/src/main/
  AndroidManifest.xml` additions and the `com/oreo/wakeword/` native
  module.
- **Porcupine wake word.** Needs a real Picovoice AccessKey and a custom
  "Oreo" `.ppn` model file (Porcupine's built-in words don't include
  "Oreo") — see `src/services/wakeword.ts`. Without both, wake-word
  detection throws a clear `WakeWordNotConfiguredError` instead of silently
  no-op'ing.
- **Mic capture.** `HomeScreen`'s manual capture button currently sends a
  placeholder file URI to exercise the API round trip end-to-end; wiring a
  real recorder (e.g. `react-native-audio-recorder-player`) to produce a
  real `.wav`/`.m4a` is a follow-up.
- **Android always-listening.** The foreground service exists as a shell
  (`WakeWordForegroundService.kt`) with clear TODOs for actually running
  Porcupine natively and bridging detections back to JS.
- **iOS always-listening.** Not solvable the same way Android is — this is
  an Apple OS policy limitation, not a gap in this code. See
  `mobile/ios/OreoWakeWordNotes/README.md` for the full explanation and the
  foreground-only fallback this app uses instead.

## Project layout

```
mobile/
  App.tsx                    # root component
  index.js                   # RN entrypoint
  src/
    api/                     # axios client, JWT refresh, per-endpoint calls
    context/AuthContext.tsx  # pairing/session state
    navigation/AppNavigator.tsx
    screens/                 # Home, Confirmation, History, Settings, Pairing
    services/
      storage.ts             # Keychain (tokens) + AsyncStorage (settings)
      wakeword.ts             # Porcupine integration point
      backgroundService.ts   # Android foreground service bridge + iOS notes
    components/WaveformIndicator.tsx
  android/                   # native additions only — see android/README.md
  ios/OreoWakeWordNotes/     # iOS background-mic limitation writeup
```

## Setup

Requires Node >= 18 and the standard React Native environment (Android
Studio + JDK for Android, Xcode for iOS — see the [React Native
"Set up your environment" guide](https://reactnative.dev/docs/set-up-your-environment)
if you haven't done this before).

```bash
cd mobile
npm install
```

### Point it at your backend

In the app's Settings screen (or by editing `src/services/storage.ts`
defaults), set the backend URL:
- **Deployment Option A (local):** `http://<your-laptop-LAN-IP>:8000`
  — the phone and backend must be on the same Wi-Fi network.
- **Deployment Option B (cloud):** your HTTPS backend URL.

You'll also need the `DEVICE_PAIRING_CODE` from the backend's `.env` to
complete pairing on first launch.

### Run (once the native projects exist — see above)

```bash
npm run android   # or: npm run ios
```

### Type-check / lint

```bash
npm run typecheck
npm run lint
```

## Known limitation summary

| Feature | Status |
|---|---|
| Screens, navigation, API client, JWT refresh | ✅ Working |
| Confirmation-gate UX | ✅ Working (talks to real backend endpoint) |
| Native Android/iOS project scaffolding | ⚠️ Needs `react-native init` generation step |
| Wake-word detection | ⚠️ Needs Picovoice AccessKey + custom "Oreo" model |
| Real mic recording | ⚠️ Stubbed with placeholder URI |
| Android background/locked-screen listening | ⚠️ Service shell only, native Porcupine wiring is a TODO |
| iOS background/locked-screen listening | ❌ Not supported by iOS — foreground-only by design |

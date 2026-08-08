# Android native scaffolding — status

This directory does **not** contain a full generated Android project (no
`gradlew`, `build.gradle`, `MainActivity.kt`, `MainApplication.kt`, etc.).
Hand-writing those from scratch reliably (correct Gradle/AGP/RN versions,
correct autolinking config) is exactly what the React Native CLI's
templates exist to do, and they change with every RN release — committing
a hand-rolled copy would just drift out of sync.

## What's actually here

- `app/src/main/AndroidManifest.xml` — the permission + `<service>`
  declarations the wake-word foreground service needs, meant to be merged
  into the generated manifest.
- `app/src/main/java/com/oreo/wakeword/`
  - `WakeWordForegroundService.kt` — the foreground service shell (starts,
    shows the required persistent notification, `START_STICKY`). Running
    Porcupine natively inside it is a TODO — see the file's docstring.
  - `OreoWakeWordServiceModule.kt` — the NativeModule bridge that
    `src/services/backgroundService.ts` calls (`NativeModules.
    OreoWakeWordService.start()/stop()`).
  - `OreoWakeWordPackage.kt` — registers that module with React Native.

## To get a real, runnable Android app

1. Generate the native project once:
   ```bash
   npx @react-native-community/cli init OreoMobileScaffold --version 0.76.5
   ```
2. Copy the generated `android/` (and `ios/`) directories into `mobile/`,
   replacing the placeholders — but keep this repo's `app/src/main/
   AndroidManifest.xml` additions and the `com/oreo/wakeword/` package,
   merging them into the generated manifest/source tree instead of
   overwriting them.
3. In the generated `MainApplication.kt`, add `OreoWakeWordPackage()` to
   the list returned from `getPackages()`.
4. `cd mobile/android && ./gradlew assembleDebug` (or `npm run android`
   from `mobile/`) to build.
5. Get a Picovoice AccessKey and a custom "Oreo" wake-word `.ppn` model
   (see `src/services/wakeword.ts`), bundle the `.ppn` file under
   `android/app/src/main/assets/`, and point Settings at it.

Until step 2 happens, `npm run android` in this repo will fail — there's no
Gradle project to build yet. The JS/TS app (screens, navigation, API
client) is fully real and can be exercised via Metro + Expo Go style
tooling or once linked into a generated project; only the native
Android/iOS shells are pending.

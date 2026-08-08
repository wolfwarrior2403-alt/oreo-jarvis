# iOS background wake-word: honest limitations

There is no native Xcode project in `mobile/ios/` yet, for the same reason
as the Android side (see `mobile/android/README.md`) — it needs to be
generated via the React Native CLI, not hand-written.

But even once that project exists, **iOS fundamentally cannot do what
Android's foreground service does**: continuous microphone access while the
app is backgrounded/the phone is locked, indefinitely, for wake-word
detection. This is an OS policy, not a gap in this codebase. Specifically:

- iOS background execution is time-boxed and purpose-restricted. Apps do
  not get arbitrary background CPU/mic access just by requesting a
  permission, unlike Android's `FOREGROUND_SERVICE_MICROPHONE`.
- The closest matching background mode is `UIBackgroundModes: audio`,
  intended for apps that play audio in the background (music players, VoIP).
  Keeping it alive by playing silent/looping audio purely to keep the mic
  "warm" for wake-word detection is a well-known workaround that:
  - drains the battery much faster than Android's approach,
  - can be rejected in App Store review as a background-mode misuse if
    there's no genuine audio content,
  - still gets suspended by the OS under memory/thermal pressure, so it is
    not reliable "always on" the way the architecture doc's phrasing
    implies.
- VoIP push / PushKit can wake an app briefly for call-like events, but
  that's not applicable to a passive wake-word listener.

## What this repo actually does on iOS

`src/services/backgroundService.ts`'s `startBackgroundListening()` throws
on iOS by default rather than pretending to support always-on background
listening. The intended UX on iOS, until/unless Apple exposes something
different:

- Wake-word detection (`src/services/wakeword.ts`, Porcupine) runs while
  the app is in the **foreground** only.
  hold-to-talk / tap-to-talk (see `HomeScreen`'s manual capture button) as
  the primary interaction on iOS, with wake-word as a nice-to-have while
  the app happens to be open.
- If true background wake-word ever becomes a hard requirement, the
  realistic paths are: (a) accept the `UIBackgroundModes: audio` tradeoffs
  above for a subset of users who opt in, or (b) wait on/monitor Apple's
  background execution APIs for something purpose-built (nothing fits as
  of this writing).

Don't try to "fix" this by finding a clever background trick without
re-reading Apple's current Background Execution documentation first — this
constraint is deliberate on Apple's part, not a bug.

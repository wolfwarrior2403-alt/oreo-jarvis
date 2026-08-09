/**
 * Always-listening background behavior (section 4.3).
 *
 * Android: wake-word detection can run in a foreground service so it keeps
 * working with the screen off/phone locked. The native side of that
 * service lives in android/app/src/main/java/com/oreo/wakeword/
 * WakeWordForegroundService.kt (a stub — see that file and
 * mobile/android/README.md for what's left to wire up: a real native
 * module bridge, the notification channel, START_STICKY handling, etc).
 * This module is the JS-side entry point that would start/stop it via
 * a NativeModules bridge once that module exists.
 *
 * iOS: Apple does not allow arbitrary continuous microphone access from
 * the background the way Android's foreground-service model does. Realistic
 * options, none of which are "always listening while locked" out of the
 * box:
 *   - Only listen while the app is in the foreground.
 *   - Use an Audio background mode (`UIBackgroundModes: audio`) combined
 *     with a silent/looping audio session to stay alive longer, which is
 *     fragile, battery-hungry, and can be rejected in App Store review if
 *     it's not tied to genuine audio playback.
 *   - Use Siri Shortcuts / a Live Activity as a lower-friction "tap or say
 *     a phrase to open Oreo" alternative instead of true always-on wake
 *     word.
 * This is a real OS constraint, not a bug in this codebase — see
 * mobile/ios/OreoWakeWordNotes/README.md for more detail. Do not attempt to
 * "fix" this without re-reading Apple's background execution docs; there
 * is no supported always-on background mic API.
 */
import {NativeModules, Platform} from 'react-native';

export interface BackgroundListeningHandle {
  stop: () => Promise<void>;
}

/**
 * Starts the platform-appropriate background listening mode.
 * Throws on iOS by default, since silently no-op-ing would misrepresent
 * what the app can actually do — callers should catch this and show the
 * user the foreground-only fallback UI instead.
 */
export async function startBackgroundListening(): Promise<BackgroundListeningHandle> {
  if (Platform.OS === 'android') {
    const {OreoWakeWordService} = NativeModules as {
      OreoWakeWordService?: {start: () => Promise<void>; stop: () => Promise<void>};
    };
    if (!OreoWakeWordService) {
      throw new Error(
        'OreoWakeWordService native module is not linked. This requires building the native Android ' +
          'project (see mobile/android/README.md) — the JS/TS app alone cannot start a foreground service.',
      );
    }
    await OreoWakeWordService.start();
    return {stop: () => OreoWakeWordService.stop()};
  }

  throw new Error(
    'True always-listening background mode is not available on iOS. See mobile/ios/OreoWakeWordNotes/README.md ' +
      'for why, and use foreground-only listening on this platform instead.',
  );
}

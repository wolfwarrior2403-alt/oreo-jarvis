/**
 * Wake-word integration point (section 4.3).
 *
 * Uses Picovoice Porcupine for on-device "Oreo" detection. Porcupine needs:
 *   1. A free Picovoice AccessKey (https://console.picovoice.ai/) — set it
 *      in Settings, stored via services/storage.ts (getPorcupineAccessKey).
 *   2. A custom wake-word model file trained for "Oreo" (Porcupine's free
 *      tier only ships built-in words like "porcupine"/"bumblebee"; a
 *      custom word needs training in the Picovoice console and bundling
 *      the resulting .ppn file into the app — see android/README and
 *      ios/OreoWakeWordNotes/).
 *
 * IMPORTANT: this module will not actually detect anything until both of
 * the above are supplied by whoever builds the app for a real device. That
 * is intentional — we don't fake a working wake-word engine without real
 * credentials. Without them, `startListening` throws a clear error instead
 * of silently doing nothing.
 */
import {getPorcupineAccessKey, getWakeWordSensitivity} from './storage';

export type WakeWordCallback = () => void;

export interface WakeWordHandle {
  stop: () => Promise<void>;
}

export class WakeWordNotConfiguredError extends Error {
  constructor() {
    super(
      'Porcupine is not configured: set a Picovoice AccessKey and wake-word model path in Settings before enabling always-listening mode.',
    );
    this.name = 'WakeWordNotConfiguredError';
  }
}

/**
 * Starts the on-device wake-word engine and invokes `onWake` every time
 * "Oreo" is detected. Returns a handle whose `stop()` tears the engine down
 * (call this from the background service's onDestroy).
 */
export async function startListening(
  onWake: WakeWordCallback,
  wakeWordModelPath: string,
): Promise<WakeWordHandle> {
  const accessKey = await getPorcupineAccessKey();
  if (!accessKey || !wakeWordModelPath) {
    throw new WakeWordNotConfiguredError();
  }

  const sensitivity = await getWakeWordSensitivity();

  // Required lazily (not at module top): the native Porcupine module isn't
  // present unless the app has been built with the native android/ios
  // projects linked (see mobile/README.md — this JS layer is shipped ahead
  // of that native scaffolding step).
  const {PorcupineManager} = require('@picovoice/porcupine-react-native');

  const manager = await PorcupineManager.fromKeywordPaths(
    accessKey,
    [wakeWordModelPath],
    (_keywordIndex: number) => onWake(),
    undefined,
    undefined,
    [sensitivity],
  );

  await manager.start();

  return {
    stop: async () => {
      await manager.stop();
      await manager.delete();
    },
  };
}

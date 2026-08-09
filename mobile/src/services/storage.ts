/**
 * Storage split by sensitivity:
 *  - JWT tokens go through react-native-keychain (OS-level secure storage —
 *    Keystore on Android, Keychain on iOS), never AsyncStorage.
 *  - Non-sensitive settings (backend URL, wake word sensitivity, retention
 *    toggle) use AsyncStorage, which is fine for plain preferences.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';

const KEYCHAIN_SERVICE = 'oreo.auth';

const SETTINGS_KEYS = {
  backendUrl: 'oreo.settings.backendUrl',
  wakeWordSensitivity: 'oreo.settings.wakeWordSensitivity',
  porcupineAccessKey: 'oreo.settings.porcupineAccessKey',
  retainRawAudio: 'oreo.settings.retainRawAudio',
  userId: 'oreo.settings.userId',
  deviceId: 'oreo.settings.deviceId',
} as const;

export interface StoredTokens {
  accessToken: string;
  refreshToken: string;
}

export async function saveTokens(tokens: StoredTokens): Promise<void> {
  await Keychain.setGenericPassword('oreo-device', JSON.stringify(tokens), {
    service: KEYCHAIN_SERVICE,
  });
}

export async function loadTokens(): Promise<StoredTokens | null> {
  const creds = await Keychain.getGenericPassword({service: KEYCHAIN_SERVICE});
  if (!creds) {
    return null;
  }
  try {
    return JSON.parse(creds.password) as StoredTokens;
  } catch {
    return null;
  }
}

export async function clearTokens(): Promise<void> {
  await Keychain.resetGenericPassword({service: KEYCHAIN_SERVICE});
}

export async function getBackendUrl(): Promise<string | null> {
  return AsyncStorage.getItem(SETTINGS_KEYS.backendUrl);
}

export async function setBackendUrl(url: string): Promise<void> {
  await AsyncStorage.setItem(SETTINGS_KEYS.backendUrl, url);
}

export async function getWakeWordSensitivity(): Promise<number> {
  const raw = await AsyncStorage.getItem(SETTINGS_KEYS.wakeWordSensitivity);
  return raw ? parseFloat(raw) : 0.5;
}

export async function setWakeWordSensitivity(value: number): Promise<void> {
  await AsyncStorage.setItem(SETTINGS_KEYS.wakeWordSensitivity, String(value));
}

export async function getPorcupineAccessKey(): Promise<string | null> {
  return AsyncStorage.getItem(SETTINGS_KEYS.porcupineAccessKey);
}

export async function setPorcupineAccessKey(key: string): Promise<void> {
  await AsyncStorage.setItem(SETTINGS_KEYS.porcupineAccessKey, key);
}

export async function getRetainRawAudio(): Promise<boolean> {
  return (await AsyncStorage.getItem(SETTINGS_KEYS.retainRawAudio)) === 'true';
}

export async function setRetainRawAudio(value: boolean): Promise<void> {
  await AsyncStorage.setItem(SETTINGS_KEYS.retainRawAudio, String(value));
}

export async function saveIdentity(userId: string, deviceId: string): Promise<void> {
  await AsyncStorage.multiSet([
    [SETTINGS_KEYS.userId, userId],
    [SETTINGS_KEYS.deviceId, deviceId],
  ]);
}

export async function getIdentity(): Promise<{userId: string | null; deviceId: string | null}> {
  const [[, userId], [, deviceId]] = await AsyncStorage.multiGet([
    SETTINGS_KEYS.userId,
    SETTINGS_KEYS.deviceId,
  ]);
  return {userId, deviceId};
}

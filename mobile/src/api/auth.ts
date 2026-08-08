import axios from 'axios';
import {saveIdentity, saveTokens} from '@/services/storage';
import type {TokenResponse} from './types';

/**
 * Device pairing (section 3.1 / 4.4). Uses a bare axios call rather than the
 * shared `client` because at pairing time there's no token yet to attach.
 */
export async function pairDevice(
  backendUrl: string,
  pairingCode: string,
  deviceName: string,
  userDisplayName?: string,
  userEmail?: string,
): Promise<TokenResponse> {
  const resp = await axios.post<TokenResponse>(`${backendUrl}/auth/pair`, {
    pairing_code: pairingCode,
    device_name: deviceName,
    user_display_name: userDisplayName ?? 'Owner',
    user_email: userEmail,
  });

  await saveTokens({
    accessToken: resp.data.access_token,
    refreshToken: resp.data.refresh_token,
  });
  await saveIdentity(resp.data.user_id, resp.data.device_id);

  return resp.data;
}

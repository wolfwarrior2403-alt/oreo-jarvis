import client from './client';
import type {VoiceProcessResponse} from './types';

/** Uploads a captured audio clip to POST /voice/process and returns the
 * transcript + Oreo's response (and, if the model wants to take an action,
 * a proposed_action_id the Confirmation screen should pick up). */
export async function processVoiceClip(fileUri: string, mimeType = 'audio/wav'): Promise<VoiceProcessResponse> {
  const form = new FormData();
  form.append('audio', {
    uri: fileUri,
    name: 'clip.wav',
    type: mimeType,
  } as unknown as Blob);

  const resp = await client.post<VoiceProcessResponse>('/voice/process', form, {
    headers: {'Content-Type': 'multipart/form-data'},
  });
  return resp.data;
}

import client from './client';
import type {UserContextResponse} from './types';

export async function getUserContext(userId: string): Promise<UserContextResponse> {
  const resp = await client.get<UserContextResponse>(`/context/user/${userId}`);
  return resp.data;
}

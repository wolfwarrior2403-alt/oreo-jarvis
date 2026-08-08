import axios, {AxiosError, AxiosInstance, InternalAxiosRequestConfig} from 'axios';
import {clearTokens, getBackendUrl, loadTokens, saveTokens} from '@/services/storage';
import type {TokenResponse} from './types';

/**
 * A single axios instance shared by the whole app. The base URL is read
 * from settings (local IP for Deployment Option A, HTTPS cloud URL for
 * Option B) rather than hardcoded — see SettingsScreen.
 */
const client: AxiosInstance = axios.create({timeout: 30_000});

let refreshInFlight: Promise<string | null> | null = null;

client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const baseUrl = await getBackendUrl();
  if (baseUrl) {
    config.baseURL = baseUrl;
  }
  const tokens = await loadTokens();
  if (tokens?.accessToken) {
    config.headers.set('Authorization', `Bearer ${tokens.accessToken}`);
  }
  return config;
});

async function refreshAccessToken(): Promise<string | null> {
  const tokens = await loadTokens();
  if (!tokens?.refreshToken) {
    return null;
  }
  const baseUrl = await getBackendUrl();
  try {
    const resp = await axios.post<TokenResponse>(`${baseUrl}/auth/refresh`, {
      refresh_token: tokens.refreshToken,
    });
    await saveTokens({
      accessToken: resp.data.access_token,
      refreshToken: resp.data.refresh_token,
    });
    return resp.data.access_token;
  } catch {
    await clearTokens();
    return null;
  }
}

client.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & {_retried?: boolean}) | undefined;
    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      // Coalesce concurrent refreshes into a single request.
      refreshInFlight = refreshInFlight ?? refreshAccessToken();
      const newAccessToken = await refreshInFlight;
      refreshInFlight = null;
      if (newAccessToken) {
        original.headers.set('Authorization', `Bearer ${newAccessToken}`);
        return client(original);
      }
    }
    return Promise.reject(error);
  },
);

export default client;

import React, {createContext, useCallback, useContext, useEffect, useMemo, useState} from 'react';
import {clearTokens, getIdentity, loadTokens} from '@/services/storage';

interface AuthState {
  isPaired: boolean;
  isLoading: boolean;
  userId: string | null;
  deviceId: string | null;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({children}: {children: React.ReactNode}) {
  const [isPaired, setIsPaired] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);
  const [deviceId, setDeviceId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    const tokens = await loadTokens();
    const identity = await getIdentity();
    setIsPaired(Boolean(tokens?.accessToken));
    setUserId(identity.userId);
    setDeviceId(identity.deviceId);
    setIsLoading(false);
  }, []);

  const logout = useCallback(async () => {
    await clearTokens();
    await refresh();
  }, [refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({isPaired, isLoading, userId, deviceId, refresh, logout}),
    [isPaired, isLoading, userId, deviceId, refresh, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

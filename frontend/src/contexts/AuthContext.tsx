/**
 * Auth context — persists session in localStorage so the user stays
 * logged in across page loads without a network round-trip.
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { apiLogin, apiGetMe, setStoredToken, clearStoredToken, getStoredToken, type UserInfo } from '../api/client';

const USER_KEY = 'pv_user';

function readStoredUser(): UserInfo | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as UserInfo) : null;
  } catch {
    return null;
  }
}

function writeStoredUser(user: UserInfo): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearStoredUser(): void {
  localStorage.removeItem(USER_KEY);
}

interface AuthState {
  user: UserInfo | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Restore user immediately from localStorage — no loading flash
  const [user, setUser] = useState<UserInfo | null>(readStoredUser);
  const [isLoading, setIsLoading] = useState(() => {
    // Only show loading if we have a token but no cached user yet
    return !!getStoredToken() && !readStoredUser();
  });

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    // Background re-validation — only clears session on explicit 401
    apiGetMe()
      .then((fresh) => {
        setUser(fresh);
        writeStoredUser(fresh);
      })
      .catch((err) => {
        const status = err?.response?.status;
        if (status === 401 || status === 403) {
          // Token genuinely invalid/expired — log out
          clearStoredToken();
          clearStoredUser();
          setUser(null);
        }
        // Any other error (network, timeout): keep the cached session
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password);
    setStoredToken(access_token);
    const me = await apiGetMe();
    setUser(me);
    writeStoredUser(me);
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    clearStoredUser();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { fetchCurrentUser, login as apiLogin, logout as apiLogout, AuthResponse, AuthUser } from '../api/auth';
import { setAuthToken } from '../api/client';
import { useNotifications } from './NotificationProvider';

interface AuthContextShape {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const STORAGE_KEY = 'floreria.auth';

const AuthContext = createContext<AuthContextShape | undefined>(undefined);

interface StoredSession {
  token: string;
  user: AuthUser;
}

const loadStoredSession = (): StoredSession | null => {
  const value = window.localStorage.getItem(STORAGE_KEY);
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(value) as StoredSession;
  } catch (error) {
    console.warn('No se pudo restaurar la sesión almacenada', error);
    return null;
  }
};

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { notify } = useNotifications();

  const clearSession = useCallback(() => {
    setToken(null);
    setUser(null);
    setAuthToken(null);
    window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  useEffect(() => {
    const stored = loadStoredSession();
    if (stored?.token) {
      setToken(stored.token);
      setAuthToken(stored.token);
      setUser(stored.user);
      setLoading(false);
      fetchCurrentUser()
        .then((current) => {
          if (current) {
            setUser(current);
          } else {
            clearSession();
          }
        })
        .catch(() => {
          clearSession();
        });
    } else {
      setLoading(false);
    }
  }, [clearSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const response: AuthResponse = await apiLogin({ email, password });
        setToken(response.token);
        setUser(response.user);
        setAuthToken(response.token);
        window.localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ token: response.token, user: response.user })
        );
        notify({ kind: 'success', title: 'Sesión iniciada', description: `Bienvenido ${response.user.firstName}` });
      } catch (error: any) {
        notify({
          kind: 'error',
          title: 'Error de autenticación',
          description: error.response?.data?.message ?? 'Credenciales incorrectas',
        });
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [notify]
  );

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch (error) {
      console.warn('Error al cerrar sesión en el servidor', error);
    }
    clearSession();
    notify({ kind: 'info', title: 'Sesión cerrada' });
  }, [clearSession, notify]);

  const value = useMemo<AuthContextShape>(
    () => ({ user, token, loading, login, logout }),
    [user, token, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextShape => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth debe utilizarse dentro de AuthProvider');
  }
  return ctx;
};

import api, { setAuthToken } from './client';

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface AuthUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

export const login = async (credentials: AuthCredentials): Promise<AuthResponse> => {
  const { data } = await api.post<AuthResponse>('/auth/login', credentials);
  setAuthToken(data.token);
  return data;
};

export const logout = async (): Promise<void> => {
  await api.post('/auth/logout');
  setAuthToken(null);
};

export const fetchCurrentUser = async (): Promise<AuthUser | null> => {
  try {
    const { data } = await api.get<AuthUser>('/auth/me');
    return data;
  } catch (error: any) {
    if (error.response?.status === 401) {
      return null;
    }
    throw error;
  }
};

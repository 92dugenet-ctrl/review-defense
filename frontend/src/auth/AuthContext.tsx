import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/services/api/client";
import type { User } from "@/types/api";
import { ACCESS_TOKEN_KEY, readAccessToken } from "@/auth/sessionToken";

type SessionPayload = {
  access_token: string;
  token_type: string;
  expires_at: string;
  role: string;
  organization_id: string;
};

type RegisterPayload = SessionPayload & {
  status: string;
};

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, organizationId: string) => Promise<void>;
  register: (email: string, organizationName: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<User | null>;
};

const ORG_KEY = "review-defense.organization-id";

const AuthContext = createContext<AuthContextValue | null>(null);

function saveSession(payload: SessionPayload) {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, payload.access_token);
  sessionStorage.setItem(ORG_KEY, payload.organization_id);
}

function clearSession() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(ORG_KEY);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!readAccessToken()) {
      setUser(null);
      return null;
    }
    try {
      const current = await api.get<User>("/v1/me", {
        headers: { Authorization: `Bearer ${readAccessToken()}` },
      });
      setUser(current);
      return current;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) clearSession();
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const login = useCallback(async (email: string, password: string, organizationId: string) => {
    const payload = await api.post<SessionPayload>("/v1/auth/login", {
      email,
      password,
      organization_id: organizationId,
    });
    saveSession(payload);
    const current = await api.get<User>("/v1/me", {
      headers: { Authorization: `Bearer ${payload.access_token}` },
    });
    setUser(current);
  }, []);

  const register = useCallback(async (email: string, organizationName: string, password: string) => {
    const payload = await api.post<RegisterPayload>("/v1/auth/register", {
      email,
      organization_name: organizationName,
      password,
    });
    if (!payload.access_token) {
      throw new ApiError("La vérification de l’adresse e-mail est requise.", 403, "EMAIL_NOT_VERIFIED");
    }
    saveSession(payload);
    const current = await api.get<User>("/v1/me", {
      headers: { Authorization: `Bearer ${payload.access_token}` },
    });
    setUser(current);
  }, []);

  const logout = useCallback(async () => {
    const token = readAccessToken();
    try {
      if (token) {
        await api.post("/v1/logout", undefined, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } finally {
      clearSession();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, isAuthenticated: Boolean(user), login, register, logout, refresh }),
    [user, loading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

export function authToken() {
  return readAccessToken();
}

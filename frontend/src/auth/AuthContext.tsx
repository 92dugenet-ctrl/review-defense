// État d'authentification React : conserve le token dans sessionStorage, expose login/logout/refresh et recharge le profil depuis /v1/me. Ce contexte sert à l'expérience de navigation ; il ne remplace jamais les vérifications d'identité et de rôle effectuées par le serveur.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ACCESS_TOKEN_KEY,
  readAccessToken,
  readCsrfToken,
  setCsrfToken,
} from "@/auth/sessionToken";
import { api, ApiError } from "@/services/api/client";
import type { User } from "@/types/api";

type SessionPayload = {
  access_token?: string;
  csrf_token?: string;
  token_type?: string;
  expires_at: string;
  role?: string;
  organization_id?: string;
};

type RegisterPayload = SessionPayload & {
  status: string;
};

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (
    email: string,
    password: string,
    organizationId: string,
  ) => Promise<void>;
  register: (
    email: string,
    organizationName: string,
    password: string,
  ) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<User | null>;
};

const ORGANIZATION_KEY = "review-defense.organization-id";

const AuthContext = createContext<AuthContextValue | null>(null);

/** Prefer the HttpOnly cookie; retain bearer storage for legacy deployments. */
function saveSession(payload: SessionPayload) {
  if (payload.access_token) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, payload.access_token);
  } else {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  }
  if (payload.organization_id) {
    sessionStorage.setItem(ORGANIZATION_KEY, payload.organization_id);
  }
  setCsrfToken(payload.csrf_token ?? null);
}

/** Remove local session values after logout or an expired/invalid session. */
function clearSession() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(ORGANIZATION_KEY);
  setCsrfToken(null);
}

/**
 * Provides the authenticated user and session actions to the React tree.
 *
 * The backend remains authoritative: this provider refreshes the current user
 * from /v1/me rather than trusting role or profile data stored in the browser.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  /** Revalidate the stored token and load the current user's profile. */
  const refresh = useCallback(async () => {
    try {
      if (!readAccessToken()) {
        const session = await api.get<{ csrf_token: string }>("/v1/auth/csrf");
        setCsrfToken(session.csrf_token);
      }

      const token = readAccessToken();
      const currentUser = await api.get<User>(
        "/v1/me",
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined,
      );
      setUser(currentUser);
      return currentUser;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearSession();
      } else if (!readAccessToken() && !readCsrfToken()) {
        setCsrfToken(null);
      }

      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  /** Authenticate an existing user and load the resulting profile. */
  const login = useCallback(
    async (email: string, password: string, organizationId: string) => {
      const payload = await api.post<SessionPayload>(
        "/v1/auth/login",
        {
          email,
          password,
          organization_id: organizationId,
        },
        { headers: { "X-Session-Mode": "cookie" } },
      );

      saveSession(payload);

      const currentUser = await api.get<User>(
        "/v1/me",
        payload.access_token
          ? { headers: { Authorization: `Bearer ${payload.access_token}` } }
          : undefined,
      );
      setUser(currentUser);
    },
    [],
  );

  /** Create an account; the API may require email verification first. */
  const register = useCallback(
    async (email: string, organizationName: string, password: string) => {
      const payload = await api.post<RegisterPayload>(
        "/v1/auth/register",
        {
          email,
          organization_name: organizationName,
          password,
        },
        { headers: { "X-Session-Mode": "cookie" } },
      );

      if (!payload.access_token && !payload.csrf_token) {
        throw new ApiError(
          "La vérification de l’adresse e-mail est requise.",
          403,
          "EMAIL_NOT_VERIFIED",
        );
      }

      saveSession(payload);

      const currentUser = await api.get<User>(
        "/v1/me",
        payload.access_token
          ? { headers: { Authorization: `Bearer ${payload.access_token}` } }
          : undefined,
      );
      setUser(currentUser);
    },
    [],
  );

  /** Ask the backend to end the session, then always clear local session data. */
  const logout = useCallback(async () => {
    const token = readAccessToken();

    try {
      if (token || readCsrfToken()) {
        await api.post(
          "/v1/logout",
          undefined,
          token ? { headers: { Authorization: `Bearer ${token}` } } : undefined,
        );
      }
    } finally {
      clearSession();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refresh,
    }),
    [user, loading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Access the authentication context from a component inside AuthProvider. */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}

/** Expose the current access token to legacy integration points when needed. */
export function authToken() {
  return readAccessToken();
}

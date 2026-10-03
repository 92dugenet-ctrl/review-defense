import { readAccessToken } from "@/auth/sessionToken";

export type ApiErrorPayload = {
  code?: string;
  message?: string;
  details?: unknown;
};

/** Normalized HTTP error shared by API calls and page-level error handling. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

/** Decode JSON responses as objects and preserve non-JSON response text. */
async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

/**
 * Shared HTTP transport for the frontend.
 *
 * It applies common headers, credentials and bearer-token authentication,
 * then converts unsuccessful HTTP responses into ApiError instances.
 */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // Keep authentication in one place so pages cannot accidentally omit it.
  if (path.startsWith("/v1/") && !headers.has("Authorization")) {
    const token = readAccessToken();

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });

  const payload = await parseResponse(response);

  if (!response.ok) {
    const error = payload as ApiErrorPayload;

    throw new ApiError(
      error.message ?? "Une erreur est survenue.",
      response.status,
      error.code,
      error.details,
    );
  }

  return payload as T;
}

/**
 * Typed convenience methods used by pages and hooks.
 * POST, PUT and PATCH serialize request bodies as JSON.
 */
export const api = {
  get: <T>(path: string, options?: RequestInit) =>
    apiRequest<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(path, {
      ...options,
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),

  put: <T>(path: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(path, {
      ...options,
      method: "PUT",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),

  patch: <T>(path: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(path, {
      ...options,
      method: "PATCH",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),

  delete: <T>(path: string, options?: RequestInit) =>
    apiRequest<T>(path, { ...options, method: "DELETE" }),
};

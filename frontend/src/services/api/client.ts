export type ApiErrorPayload = {
  code?: string;
  message?: string;
  details?: unknown;
};

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

async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) return response.json();
  return response.text();
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
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

export const api = {
  get: <T>(path: string, options?: RequestInit) => apiRequest<T>(path, { ...options, method: "GET" }),
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
    apiRequest<T>(path, { ...options, method: "PATCH", body: body === undefined ? undefined : JSON.stringify(body) }),
  delete: <T>(path: string, options?: RequestInit) =>
    apiRequest<T>(path, { ...options, method: "DELETE" }),
};
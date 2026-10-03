/**
 * Client HTTP partagé par les fonctionnalités de la console web.
 *
 * Les écrans et services frontend appellent api.get/post/put/patch/delete
 * plutôt que fetch directement. Ce point central applique les mêmes règles
 * de cookies, d'en-têtes, de décodage des réponses et de normalisation
 * des erreurs pour l'ensemble des appels vers l'API backend.
 */

export type ApiErrorPayload = {
  /** Code fonctionnel renvoyé par l'API, lorsqu'il existe. */
  code?: string;
  /** Message destiné à expliquer l'erreur à l'appelant. */
  message?: string;
  /** Informations complémentaires propres à l'erreur. */
  details?: unknown;
};

/**
 * Erreur HTTP structurée utilisée par les composants appelants.
 * Le statut permet de distinguer, par exemple, une session expirée
 * d'une erreur de validation ou d'une indisponibilité serveur.
 */
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

// Une URL vide signifie que les routes API sont servies sur la même origine.
// On retire le slash final pour éviter les doubles slashs lors de la concaténation.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

/**
 * Décode le corps selon le Content-Type annoncé par le serveur.
 * Les réponses JSON deviennent des objets ; les autres réponses restent du texte.
 */
async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

/**
 * Exécute une requête HTTP et convertit les réponses non-2xx en ApiError.
 *
 * credentials: include transmet les cookies de session au backend.
 * Les en-têtes fournis par l'appelant sont conservés et peuvent compléter
 * les valeurs communes. Le type générique T décrit la forme attendue
 * par le service frontend ; il ne valide pas le JSON à l'exécution.
 */
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

/**
 * Façade HTTP utilisée par les écrans et services métier frontend.
 * Chaque méthode fixe le verbe HTTP ; les méthodes avec corps sérialisent
 * l'objet JavaScript en JSON avant de le transmettre à l'API.
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

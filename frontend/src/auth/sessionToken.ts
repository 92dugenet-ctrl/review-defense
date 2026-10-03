// Accès centralisé au token de session du navigateur. Le module limite les lectures directes de sessionStorage dans les composants ; le token est transmis à l'API et validé côté serveur à chaque requête protégée.

export const ACCESS_TOKEN_KEY = "review-defense.access-token";

let csrfToken: string | null = null;

/** Read the legacy bearer token when cookie authentication is not enabled. */
export function readAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

/** Keep the CSRF proof in memory; it is never persisted to browser storage. */
export function setCsrfToken(value: string | null): void {
  csrfToken = value;
}

/** Return the in-memory CSRF proof for same-origin cookie-authenticated writes. */
export function readCsrfToken(): string | null {
  return csrfToken;
}

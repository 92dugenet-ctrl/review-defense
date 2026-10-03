// Accès centralisé au token de session du navigateur. Le module limite les lectures directes de sessionStorage dans les composants ; le token est transmis à l'API et validé côté serveur à chaque requête protégée.

export const ACCESS_TOKEN_KEY = "review-defense.access-token";

/** Read the current browser session token without exposing storage details to API callers. */
export function readAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export const ACCESS_TOKEN_KEY = "review-defense.access-token";

/** Read the current browser session token without exposing storage details to API callers. */
export function readAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

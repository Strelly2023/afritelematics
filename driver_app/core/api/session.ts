let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token && token.trim() ? token.trim() : null;
}

export function getAuthToken(): string | null {
  return authToken;
}

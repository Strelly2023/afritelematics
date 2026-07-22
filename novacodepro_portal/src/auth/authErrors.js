const SAFE_MESSAGES = {
  INVALID_CREDENTIALS: "Email or password is incorrect.",
  RATE_LIMITED: "Too many sign-in attempts. Please wait and try again.",
  SESSION_EXPIRED: "Your session has expired. Sign in again to continue.",
  API_UNAVAILABLE: "We cannot reach NovaID right now. Check that the local API services are running, then try again.",
  ACCOUNT_LOCKED: "This account is temporarily locked. Contact your NovaID administrator.",
  APPLICATION_ERROR: "We could not complete sign-in. Try again or contact support.",
};

function stringValue(value) {
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

export function normalizeApiError(error, response) {
  const detail = error?.detail && typeof error.detail === "object" ? error.detail : error;
  const status = Number(response?.status || error?.status || detail?.status || 0);
  const sourceCode = stringValue(detail?.code || error?.code).toUpperCase();
  const sourceMessage = stringValue(detail?.message || (error instanceof Error ? error.message : ""));
  let code = sourceCode || "APPLICATION_ERROR";
  if (status === 401) code = "INVALID_CREDENTIALS";
  else if (status === 423) code = "ACCOUNT_LOCKED";
  else if (status === 429) code = "RATE_LIMITED";
  else if (!response && (error instanceof TypeError || sourceCode === "API_UNAVAILABLE" || error?.name === "AbortError")) code = "API_UNAVAILABLE";
  else if (/SESSION_(EXPIRED|REQUIRED|REVOKED)/.test(sourceCode) || /session(_| )?(expired|required|revoked)/i.test(sourceMessage)) code = "SESSION_EXPIRED";
  return {
    code,
    status,
    message: sourceMessage,
    correlationId: stringValue(detail?.correlation_id || detail?.correlationId || error?.correlation_id || error?.correlationId),
  };
}

export function getUserSafeMessage(error) {
  const normalized = error?.code ? error : normalizeApiError(error);
  return SAFE_MESSAGES[normalized.code] || SAFE_MESSAGES.APPLICATION_ERROR;
}

export function getCorrelationId(error) {
  return stringValue(error?.correlationId || error?.correlation_id);
}

export function createClientReferenceId() {
  return `NCP-AUTH-${Date.now().toString(36).toUpperCase()}`;
}

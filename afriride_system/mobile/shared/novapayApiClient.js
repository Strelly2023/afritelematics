const DEFAULT_BASE_URL =
  process.env.EXPO_PUBLIC_NOVAPAY_API_URL ||
  process.env.EXPO_PUBLIC_NOVAPAY_API_BASE_URL ||
  "https://api.afritechnology.com/v1/core-platform";
const DEFAULT_TIMEOUT_MS = 5000;
const DEFAULT_RETRIES = 1;

let apiBaseUrl = DEFAULT_BASE_URL;
const tokenCache = new Map();

export function getNovapayApiBaseUrl() {
  return apiBaseUrl;
}

export function setNovapayApiBaseUrl(value) {
  apiBaseUrl = (value || DEFAULT_BASE_URL).replace(/\/$/, "");
  tokenCache.clear();
}

function randomId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function readPayload(response) {
  const body = await response.text();
  if (!body) {
    return {};
  }
  try {
    return JSON.parse(body);
  } catch {
    throw new Error(`non_json_response_${response.status}`);
  }
}

function extractMessage(payload) {
  if (payload?.error?.message) {
    return payload.error.message;
  }
  if (payload?.detail) {
    return typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
  }
  return "request_failed";
}

async function issueToken(role, userId) {
  const cacheKey = `${role}:${userId}`;
  if (tokenCache.has(cacheKey)) {
    return tokenCache.get(cacheKey);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const response = await fetch(`${apiBaseUrl}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, role }),
      signal: controller.signal,
    });
    const payload = await readPayload(response);
    if (!response.ok || !payload.token) {
      throw new Error(extractMessage(payload));
    }
    tokenCache.set(cacheKey, payload.token);
    return payload.token;
  } finally {
    clearTimeout(timeout);
  }
}

async function request(path, options = {}, retries = DEFAULT_RETRIES) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  const method = options.method || "GET";

  try {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    if (options.role && options.userId) {
      headers.Authorization = `Bearer ${await issueToken(options.role, options.userId)}`;
    }

    const response = await fetch(`${apiBaseUrl}${path}`, {
      headers,
      method,
      signal: controller.signal,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      throw new Error(extractMessage(payload));
    }
    return payload;
  } catch (error) {
    if (retries > 0 && error?.name === "AbortError") {
      return request(path, options, retries - 1);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export function getTransferFeatures() {
  return request("/transfers/features");
}

export function getTransferLimits() {
  return request("/transfers/limits");
}

export function getTransferRails() {
  return request("/transfers/rails");
}

export function quoteTransfer({
  role,
  userId,
  recipientName,
  recipientIdentifier,
  recipientCountry,
  amount,
  sourceCurrency,
  payoutMethod,
  useCase,
  memo,
}) {
  return request("/transfers/quote", {
    method: "POST",
    role,
    userId,
    headers: {
      "Idempotency-Key": randomId("novapay-quote"),
    },
    body: {
      recipient_name: recipientName,
      recipient_identifier: recipientIdentifier,
      recipient_country: recipientCountry,
      amount,
      source_currency: sourceCurrency,
      payout_method: payoutMethod,
      use_case: useCase,
      memo,
    },
  });
}

export function executeTransfer({
  role,
  userId,
  quote,
  provider,
  liveProvider = false,
}) {
  const body = {
    quote,
    live_provider: liveProvider,
  };
  if (provider) {
    body.provider = provider;
  }
  return request("/transfers/execute", {
    method: "POST",
    role,
    userId,
    headers: {
      "Idempotency-Key": randomId("novapay-execute"),
    },
    body,
  });
}

export function verifyTransferReceipt({
  role,
  userId,
  receipt,
}) {
  return request("/transfers/verify", {
    method: "POST",
    role,
    userId,
    body: {
      receipt,
    },
  });
}

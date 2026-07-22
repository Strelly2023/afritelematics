import assert from "node:assert/strict";
import test from "node:test";

import { getCorrelationId, getUserSafeMessage, normalizeApiError } from "../src/auth/authErrors.js";

test("authentication errors are normalized without rendering raw objects", () => {
  const normalized = normalizeApiError({ detail: { code: "bad_credentials", message: { unsafe: true }, correlation_id: "corr-17" } }, { status: 401 });
  assert.equal(normalized.code, "INVALID_CREDENTIALS");
  assert.equal(getUserSafeMessage(normalized), "Email or password is incorrect.");
  assert.equal(getCorrelationId(normalized), "corr-17");
  assert.doesNotMatch(getUserSafeMessage(normalized), /\[object Object\]/);
});

test("network and rate-limit failures receive safe actionable messages", () => {
  assert.match(getUserSafeMessage(normalizeApiError(new TypeError("fetch failed"))), /cannot reach NovaID/i);
  assert.match(getUserSafeMessage(normalizeApiError({}, { status: 429 })), /too many sign-in attempts/i);
});

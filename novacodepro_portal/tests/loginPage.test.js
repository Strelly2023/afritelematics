import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/auth/LoginPage.jsx", import.meta.url), "utf8");

test("secure login experience exposes required NovaID controls and states", () => {
  for (const token of [
    "Email or username",
    "Show password",
    "Remember this device",
    "Forgot password?",
    "Passkey",
    "Enterprise SSO",
    "MFA and adaptive verification",
    "Verifying identity",
    'role="alert"',
  ]) {
    assert.ok(source.includes(token), `expected login page to include ${token}`);
  }
});

test("unsupported identity capabilities are represented honestly", () => {
  assert.ok(source.includes("is not enabled for this NovaCodePro workspace"));
  assert.ok(source.includes("managed by your NovaID administrator"));
});

import assert from "node:assert/strict";
import test from "node:test";

import { isPublicAuthPath, resolveSafeReturnTo } from "../src/auth/authRouting.js";

test("public authentication routes are independent from protected workspaces", () => {
  for (const path of ["/novacodepro/login", "/novacodepro/forgot-password", "/novacodepro/reset-password", "/novacodepro/auth/callback", "/novacodepro/auth/help"]) {
    assert.equal(isPublicAuthPath(path), true);
  }
});

test("return destinations accept only internal protected NovaCodePro paths", () => {
  assert.equal(resolveSafeReturnTo("/novacodepro/design/studio"), "/novacodepro/design/studio");
  assert.equal(resolveSafeReturnTo("https://attacker.example/phish"), "/novacodepro/dashboard");
  assert.equal(resolveSafeReturnTo("//attacker.example/phish"), "/novacodepro/dashboard");
  assert.equal(resolveSafeReturnTo("/novacodepro/login"), "/novacodepro/dashboard");
});

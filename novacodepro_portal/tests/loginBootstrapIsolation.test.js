import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");

test("public authentication route renders before bootstrap recovery", () => {
  const publicRoute = source.indexOf('if (publicAuthRoute && authStatus !== "signed-in")');
  const recoveryRoute = source.indexOf('if (["API_UNAVAILABLE", "APPLICATION_ERROR"');
  assert.ok(publicRoute > 0);
  assert.ok(recoveryRoute > publicRoute);
});

test("login uses safe return destinations and normalized API failures", () => {
  assert.match(source, /resolveSafeReturnTo/);
  assert.match(source, /normalizeApiError/);
  assert.match(source, /getUserSafeMessage/);
  assert.match(source, /Diagnostic reference:/);
  assert.match(source, /userSafeText/);
  assert.doesNotMatch(source, /setBootstrapError\(detail\.message \|\|/);
});

test("authenticated bootstrap preserves registered NovaCodePro application routes", () => {
  assert.match(source, /isSolutionRoute\(currentPathname\) \|\| parseNovaCodeProRoute\(currentPathname\)/);
});

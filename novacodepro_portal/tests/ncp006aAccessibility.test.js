import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

test("NCP-006A portal source retains accessible state and form structure", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP006APortal.jsx", import.meta.url), "utf8");
  for (const token of [
    'role="status"',
    'aria-live="polite"',
    "form-field",
    "stack-item",
    "empty-state",
    "Traceability Bridge",
    "Architecture Models",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

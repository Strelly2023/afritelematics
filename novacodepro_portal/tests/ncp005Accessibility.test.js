import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

test("NCP-005 portal surfaces include accessible structure for requirements and knowledge views", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP005Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    'role="status"',
    'aria-live="polite"',
    "empty-state",
    "form-field",
    "panel-header",
    "Knowledge search",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

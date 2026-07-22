import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/strategy/StrategyWorkspace.jsx", import.meta.url), "utf8");

test("strategy workspace renders the enterprise planning shell", () => {
  assert.match(source, /Enterprise Strategy Workspace/);
  assert.match(source, /Enterprise Vision/);
  assert.match(source, /Product Strategy Center/);
  assert.match(source, /Trace matrix/);
  assert.match(source, /Approval workflow/);
  assert.match(source, /product-strategy-center/);
  assert.match(source, /roadmap-center/);
});

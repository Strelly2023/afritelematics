import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("portal registry stays identical to the repository contract", () => {
  const rootRegistry = readFileSync(new URL("../../contracts/app-registry.json", import.meta.url), "utf8");
  const portalRegistry = readFileSync(new URL("../contracts/app-registry.json", import.meta.url), "utf8");
  assert.equal(portalRegistry, rootRegistry);
});

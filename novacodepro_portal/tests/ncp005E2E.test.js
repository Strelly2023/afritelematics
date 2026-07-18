import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

test("NCP-005 end-to-end route surface covers requirements and knowledge flows", () => {
  const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
  const portalSource = readFileSync(new URL("../src/novacodepro/NCP005Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    "NCP005Portal",
  ]) {
    assert.ok(appSource.includes(token), `expected app source to include ${token}`);
  }
  for (const token of [
    "/novacodepro/requirements",
    "/novacodepro/knowledge",
    "/novacodepro/knowledge/search",
    "/novacodepro/requirements/new",
    "/novacodepro/knowledge/documents/new",
  ]) {
    assert.ok(portalSource.includes(token), `expected portal source to include ${token}`);
  }
});

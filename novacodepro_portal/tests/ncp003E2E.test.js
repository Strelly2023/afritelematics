import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("NCP-003 portal surface exposes workspace project and request flows", () => {
  const source = readFileSync(new URL("../src/novacodepro/NCP003Portal.jsx", import.meta.url), "utf8");
  for (const token of [
    "/novacodepro/workspace",
    "/novacodepro/projects",
    "/novacodepro/requests",
    "handleCreateProject",
    "handleCreateRequest",
    "handleArchiveProject",
    "handleSubmitRequest",
    "handleTransitionRequest",
  ]) {
    assert.ok(source.includes(token), `expected portal source to include ${token}`);
  }
});

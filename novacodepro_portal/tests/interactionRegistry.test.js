import assert from "node:assert/strict";
import test from "node:test";

import {
  createDefaultInteractionRegistry,
  createInteractionRegistry,
} from "../src/platform/interaction/index.js";
import { NOVACODEPRO_INTERACTION_MANIFEST } from "../src/platform/productFrontendManifests.js";

test("interaction registry registers and executes handlers", async () => {
  const registry = createDefaultInteractionRegistry();
  const manifest = registry.register(NOVACODEPRO_INTERACTION_MANIFEST);
  registry.registerHandler("novacodepro.ai.ask", async (context) => ({ status: "PASS", context }));

  assert.equal(manifest.productCode, "novacodepro");
  assert.equal(registry.resolve("novacodepro", "novacodepro.ai.ask").type, "SUBMIT");

  const result = await registry.execute("novacodepro.ai.ask", { requestId: "req-1" });
  assert.equal(result.status, "PASS");
  assert.equal(result.context.requestId, "req-1");
});

test("interaction registry reports not connected without a handler", async () => {
  const registry = createInteractionRegistry();
  registry.register(NOVACODEPRO_INTERACTION_MANIFEST);

  const result = await registry.execute("novacodepro.workspace.open", {});
  assert.equal(result.status, "NOT_CONNECTED");
});

test("interaction registry rejects duplicate interactions", () => {
  const registry = createInteractionRegistry();
  registry.register(NOVACODEPRO_INTERACTION_MANIFEST);

  assert.throws(
    () =>
      registry.register({
        ...NOVACODEPRO_INTERACTION_MANIFEST,
        productCode: "novacodepro-copy",
        interactions: NOVACODEPRO_INTERACTION_MANIFEST.interactions.map((interaction) => ({
          ...interaction,
          productCode: "novacodepro-copy",
        })),
      }),
    /Interaction conflict detected/i,
  );
});


import assert from "node:assert/strict";
import test from "node:test";

import {
  createDefaultRenderingRegistry,
  createRenderingRegistry,
} from "../src/platform/rendering/index.js";
import { NOVACODEPRO_RENDERING_MANIFEST } from "../src/platform/productFrontendManifests.js";

test("rendering registry registers product screen and interaction contracts", () => {
  const registry = createDefaultRenderingRegistry();
  const manifest = registry.register(NOVACODEPRO_RENDERING_MANIFEST);

  assert.equal(manifest.productCode, "novacodepro");
  assert.equal(registry.getScreen("novacodepro.dashboard").title, "NovaCodePro Dashboard");
  assert.equal(registry.listProductScreens("novacodepro").length > 0, true);
  assert.equal(registry.listInteractions("novacodepro").some((item) => item.interactionId === "novacodepro.ai.ask"), true);
});

test("rendering registry rejects duplicate screens and invalid layouts", () => {
  const registry = createRenderingRegistry();
  registry.register(NOVACODEPRO_RENDERING_MANIFEST);

  assert.throws(
    () =>
      registry.register({
        ...NOVACODEPRO_RENDERING_MANIFEST,
        productCode: "novacodepro-copy",
        screens: NOVACODEPRO_RENDERING_MANIFEST.screens.map((screen) => ({
          ...screen,
          productCode: "novacodepro-copy",
        })),
      }),
    /Screen conflict detected/i,
  );

  assert.throws(
    () =>
      createRenderingRegistry().register({
        ...NOVACODEPRO_RENDERING_MANIFEST,
        productCode: "broken",
        screens: [
          {
            ...NOVACODEPRO_RENDERING_MANIFEST.screens[0],
            productCode: "broken",
            layout: "unknown-layout",
          },
        ],
      }),
    /Unsupported layout/i,
  );
});


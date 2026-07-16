import assert from "node:assert/strict";
import test from "node:test";

import {
  createDefaultProductFrontendRegistry,
  createProductFrontendManifest,
  createProductFrontendRegistry,
} from "../src/platform/productFrontendRegistry.js";

test("product frontend registry registers product manifests", () => {
  const registry = createDefaultProductFrontendRegistry();
  const manifest = registry.register(
    createProductFrontendManifest({
      productCode: "novafleet",
      version: "2026.07.0",
      displayName: "NovaFleet",
      routePrefix: "/novafleet",
      navigationItems: [
        {
          id: "fleet-dashboard",
          label: "Dashboard",
          path: "/novafleet",
          permission: "novafleet:dashboard:view",
        },
      ],
      routes: [
        {
          routeId: "novafleet.dashboard",
          productCode: "novafleet",
          path: "/novafleet",
          title: "Dashboard",
          audience: "EMPLOYEE",
          requiredPermissions: ["novafleet:dashboard:view"],
        },
      ],
      requiredPermissions: ["novafleet:dashboard:view"],
      featureFlags: ["novafleet.enabled"],
      supportedLocales: ["en-AU"],
      apiDependencies: [
        {
          name: "novafleet-api",
          basePath: "/v1/novafleet",
          version: "v1",
        },
      ],
      telemetryNamespace: "novafleet",
      apps: ["employee-portal"],
    }),
  );

  assert.equal(manifest.productCode, "novafleet");
  assert.equal(registry.get("novafleet").displayName, "NovaFleet");
  assert.equal(registry.list().some((item) => item.productCode === "novafleet"), true);
});

test("product frontend registry rejects protected and conflicting routes", () => {
  const registry = createProductFrontendRegistry();
  registry.register(
    createProductFrontendManifest({
      productCode: "novafleet",
      version: "2026.07.0",
      displayName: "NovaFleet",
      routePrefix: "/novafleet",
      navigationItems: [],
      routes: [
        {
          routeId: "novafleet.dashboard",
          productCode: "novafleet",
          path: "/novafleet",
          title: "Dashboard",
          audience: "EMPLOYEE",
          requiredPermissions: [],
        },
      ],
      requiredPermissions: [],
      featureFlags: [],
      supportedLocales: ["en-AU"],
      apiDependencies: [],
      telemetryNamespace: "novafleet",
      apps: [],
    }),
  );

  assert.throws(
    () =>
      registry.register(
        createProductFrontendManifest({
          productCode: "platform-ui",
          version: "2026.07.0",
          displayName: "Platform UI",
          routePrefix: "/platform-ui",
          navigationItems: [],
          routes: [
            {
              routeId: "platform-ui.health",
              productCode: "platform-ui",
              path: "/health",
              title: "Health",
              audience: "INTERNAL",
              requiredPermissions: [],
            },
          ],
          requiredPermissions: [],
          featureFlags: [],
          supportedLocales: ["en-AU"],
          apiDependencies: [],
          telemetryNamespace: "platform-ui",
          apps: [],
        }),
      ),
    /shared frontend prefix/i,
  );

  assert.throws(
    () =>
      registry.register(
        createProductFrontendManifest({
          productCode: "novafleet-copy",
          version: "2026.07.0",
          displayName: "NovaFleet Copy",
          routePrefix: "/novafleet",
          navigationItems: [],
          routes: [
            {
              routeId: "novafleet-copy.dashboard",
              productCode: "novafleet-copy",
              path: "/novafleet",
              title: "Dashboard",
              audience: "EMPLOYEE",
              requiredPermissions: [],
            },
          ],
          requiredPermissions: [],
          featureFlags: [],
          supportedLocales: ["en-AU"],
          apiDependencies: [],
          telemetryNamespace: "novafleet-copy",
          apps: [],
        }),
      ),
    /Route conflict detected/i,
  );
});


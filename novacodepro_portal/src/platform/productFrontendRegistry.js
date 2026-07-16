const SHARED_FRONTEND_PREFIXES = [
  "/login",
  "/logout",
  "/auth",
  "/account",
  "/platform",
  "/admin/platform",
  "/system",
  "/health",
  "/status",
  "/config",
  "/docs",
  "/redoc",
  "/openapi.json",
];

function toString(value, fallback = "") {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

function assertArray(value, field) {
  if (!Array.isArray(value)) {
    throw new Error(`Product frontend manifest missing ${field}.`);
  }
  return value;
}

function normalizeRoutePath(path) {
  const normalized = toString(path);
  if (!normalized.startsWith("/")) {
    throw new Error(`Route path "${normalized}" must start with "/".`);
  }
  return normalized === "/" ? "/" : normalized.replace(/\/+$/, "") || "/";
}

function assertPrefixOwnership(routePrefix, path) {
  const normalizedPath = normalizeRoutePath(path);
  if (SHARED_FRONTEND_PREFIXES.some((prefix) => normalizedPath === prefix || normalizedPath.startsWith(`${prefix}/`))) {
    throw new Error(`Route path "${normalizedPath}" conflicts with a shared frontend prefix.`);
  }
  if (!normalizedPath.startsWith(routePrefix)) {
    throw new Error(`Route path "${normalizedPath}" must belong to prefix "${routePrefix}".`);
  }
}

function normalizeManifest(manifest) {
  const normalizedRoutePrefix = normalizeRoutePath(manifest.routePrefix);
  const routes = assertArray(manifest.routes || [], "routes").map((route) => {
    const path = normalizeRoutePath(route.path);
    assertPrefixOwnership(normalizedRoutePrefix, path);
    return {
      routeId: toString(route.routeId),
      productCode: toString(route.productCode || manifest.productCode),
      path,
      title: toString(route.title || route.label || route.routeId),
      audience: toString(route.audience || "INTERNAL"),
      layout: toString(route.layout || "shared"),
      featureFlag: toString(route.featureFlag || ""),
      requiredPermissions: assertArray(route.requiredPermissions || [], "requiredPermissions").map((item) => toString(item)),
    };
  });

  const navigationItems = assertArray(manifest.navigationItems || [], "navigationItems").map((item) => ({
    id: toString(item.id),
    label: toString(item.label || item.id),
    path: normalizeRoutePath(item.path),
    permission: toString(item.permission || ""),
  }));

  return {
    productCode: toString(manifest.productCode),
    version: toString(manifest.version),
    displayName: toString(manifest.displayName),
    routePrefix: normalizedRoutePrefix,
    navigationItems,
    routes,
    requiredPermissions: assertArray(manifest.requiredPermissions || [], "requiredPermissions").map((item) => toString(item)),
    featureFlags: assertArray(manifest.featureFlags || [], "featureFlags").map((item) => toString(item)),
    supportedLocales: assertArray(manifest.supportedLocales || [], "supportedLocales").map((item) => toString(item)),
    branding: {
      productName: toString(manifest.branding?.productName || manifest.displayName),
      logo: toString(manifest.branding?.logo || ""),
      icon: toString(manifest.branding?.icon || "app"),
      accentToken: toString(manifest.branding?.accentToken || "product.default"),
      heroVariant: toString(manifest.branding?.heroVariant || ""),
    },
    apiDependencies: assertArray(manifest.apiDependencies || [], "apiDependencies").map((item) => ({
      name: toString(item.name),
      basePath: normalizeRoutePath(item.basePath || "/v1"),
      version: toString(item.version || "v1"),
    })),
    telemetryNamespace: toString(manifest.telemetryNamespace || manifest.productCode),
    apps: assertArray(manifest.apps || [], "apps").map((item) => toString(item)),
    configurationSchema: manifest.configurationSchema || { version: 1, fields: [] },
  };
}

export function createProductFrontendRegistry() {
  const manifests = new Map();
  const routeIndex = new Map();
  const navigationIndex = new Map();
  const permissionIndex = new Map();
  const featureFlagIndex = new Map();

  function register(manifest) {
    const normalized = normalizeManifest(manifest);
    if (!normalized.productCode) {
      throw new Error("Product frontend manifest missing productCode.");
    }
    if (manifests.has(normalized.productCode)) {
      throw new Error(`Product frontend manifest already registered for ${normalized.productCode}.`);
    }

    for (const route of normalized.routes) {
      const routeKey = `${route.path}`;
      if (routeIndex.has(routeKey)) {
        throw new Error(`Route conflict detected for ${route.path}.`);
      }
      routeIndex.set(routeKey, normalized.productCode);
    }

    for (const item of normalized.navigationItems) {
      if (navigationIndex.has(item.id)) {
        throw new Error(`Navigation conflict detected for ${item.id}.`);
      }
      navigationIndex.set(item.id, normalized.productCode);
    }

    for (const permission of normalized.requiredPermissions) {
      if (permissionIndex.has(permission) && permissionIndex.get(permission) !== normalized.productCode) {
        throw new Error(`Permission conflict detected for ${permission}.`);
      }
      permissionIndex.set(permission, normalized.productCode);
    }

    for (const featureFlag of normalized.featureFlags) {
      if (featureFlagIndex.has(featureFlag) && featureFlagIndex.get(featureFlag) !== normalized.productCode) {
        throw new Error(`Feature flag conflict detected for ${featureFlag}.`);
      }
      featureFlagIndex.set(featureFlag, normalized.productCode);
    }

    manifests.set(normalized.productCode, normalized);
    return normalized;
  }

  function unregister(productCode) {
    const normalizedProductCode = toString(productCode);
    const manifest = manifests.get(normalizedProductCode);
    if (!manifest) {
      return false;
    }
    manifests.delete(normalizedProductCode);
    for (const [routeKey, owner] of [...routeIndex.entries()]) {
      if (owner === normalizedProductCode) {
        routeIndex.delete(routeKey);
      }
    }
    for (const [navId, owner] of [...navigationIndex.entries()]) {
      if (owner === normalizedProductCode) {
        navigationIndex.delete(navId);
      }
    }
    for (const [permission, owner] of [...permissionIndex.entries()]) {
      if (owner === normalizedProductCode) {
        permissionIndex.delete(permission);
      }
    }
    for (const [flag, owner] of [...featureFlagIndex.entries()]) {
      if (owner === normalizedProductCode) {
        featureFlagIndex.delete(flag);
      }
    }
    return manifest;
  }

  function get(productCode) {
    return manifests.get(toString(productCode)) || null;
  }

  function list() {
    return [...manifests.values()];
  }

  function getRoutes() {
    return list().flatMap((manifest) => manifest.routes.map((route) => ({ ...route, productCode: manifest.productCode })));
  }

  return { register, unregister, get, list, getRoutes };
}

export function createDefaultProductFrontendRegistry() {
  return createProductFrontendRegistry();
}

export function createProductFrontendManifest(manifest) {
  return normalizeManifest(manifest);
}

export function normalizePluginManifest(manifest = {}) {
  return {
    id: manifest.id || manifest.name || "plugin",
    name: manifest.name || manifest.id || "Runtime Plugin",
    version: manifest.version || "1.0.0",
    capabilities: Array.isArray(manifest.capabilities) ? manifest.capabilities : [],
    commands: Array.isArray(manifest.commands) ? manifest.commands : [],
    events: Array.isArray(manifest.events) ? manifest.events : [],
    policies: Array.isArray(manifest.policies) ? manifest.policies : [],
    permissions: Array.isArray(manifest.permissions) ? manifest.permissions : [],
    configuration: manifest.configuration || {},
    dependencies: Array.isArray(manifest.dependencies) ? manifest.dependencies : [],
    migration: manifest.migration || null,
    health: manifest.health || "unknown",
    compatibility: manifest.compatibility || {},
  };
}

export function validatePluginManifest(manifest = {}) {
  const normalized = normalizePluginManifest(manifest);
  const issues = [];

  if (!normalized.id) issues.push("Plugin id is required.");
  if (!normalized.name) issues.push("Plugin name is required.");
  if (!normalized.version) issues.push("Plugin version is required.");
  if (normalized.permissions.some((permission) => typeof permission !== "string" || !permission.trim())) {
    issues.push("Plugin permissions must be non-empty strings.");
  }

  return {
    valid: issues.length === 0,
    issues,
    manifest: normalized,
  };
}

export function createPluginSdk({ allowedPermissions = [] } = {}) {
  const registry = new Map();
  let permissions = new Set(Array.isArray(allowedPermissions) ? allowedPermissions : []);

  const authorize = (manifest = {}) => {
    const requested = Array.isArray(manifest.permissions) ? manifest.permissions : [];
    const unauthorized = requested.filter((permission) => !permissions.has(permission));
    return {
      allowed: unauthorized.length === 0,
      unauthorized,
    };
  };

  return {
    register(manifest = {}) {
      const validation = validatePluginManifest(manifest);
      if (!validation.valid) {
        return validation;
      }
      const authorization = authorize(validation.manifest);
      if (!authorization.allowed) {
        return {
          valid: false,
          issues: [`Plugin permissions not allowed: ${authorization.unauthorized.join(", ")}`],
          manifest: validation.manifest,
        };
      }
      registry.set(validation.manifest.id, validation.manifest);
      return { valid: true, manifest: validation.manifest };
    },
    get(id) {
      return registry.get(id) || null;
    },
    list() {
      return [...registry.values()];
    },
    validate: validatePluginManifest,
    authorize,
    setAllowedPermissions(nextPermissions = []) {
      permissions = new Set(Array.isArray(nextPermissions) ? nextPermissions : []);
      return [...permissions];
    },
    get allowedPermissions() {
      return [...permissions];
    },
  };
}

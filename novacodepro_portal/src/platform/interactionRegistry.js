import { createProductInteractionManifest } from "./interactionManifest.js";

function toString(value, fallback = "") {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

export function createInteractionRegistry() {
  const manifests = new Map();
  const interactionIndex = new Map();
  const handlers = new Map();

  function register(manifest) {
    const normalized = createProductInteractionManifest(manifest);
    if (manifests.has(normalized.productCode)) {
      throw new Error(`Product interaction manifest already registered for ${normalized.productCode}.`);
    }
    for (const interaction of normalized.interactions) {
      if (!interaction.interactionId) {
        throw new Error("Interaction manifest contains an interaction without interactionId.");
      }
      if (interactionIndex.has(interaction.interactionId)) {
        throw new Error(`Interaction conflict detected for ${interaction.interactionId}.`);
      }
      interactionIndex.set(interaction.interactionId, normalized.productCode);
    }
    manifests.set(normalized.productCode, normalized);
    return normalized;
  }

  function unregister(productCode) {
    const normalizedProductCode = toString(productCode);
    const manifest = manifests.get(normalizedProductCode);
    if (!manifest) {
      return null;
    }
    manifests.delete(normalizedProductCode);
    for (const [key, owner] of [...interactionIndex.entries()]) {
      if (owner === normalizedProductCode) {
        interactionIndex.delete(key);
        handlers.delete(key);
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

  function resolve(productCode, interactionId) {
    const manifest = get(productCode);
    if (!manifest) {
      return null;
    }
    return manifest.interactions.find((item) => item.interactionId === toString(interactionId)) || null;
  }

  function registerHandler(interactionId, handler) {
    handlers.set(toString(interactionId), handler);
  }

  async function execute(interactionId, context = {}) {
    const normalizedInteractionId = toString(interactionId);
    const handler = handlers.get(normalizedInteractionId);
    if (!handler) {
      return {
        status: "NOT_CONNECTED",
        interactionId: normalizedInteractionId,
        reason: "No interaction handler is registered.",
      };
    }
    return handler(context);
  }

  function snapshot() {
    return {
      productCount: manifests.size,
      interactionCount: interactionIndex.size,
      products: list().map((manifest) => ({
        productCode: manifest.productCode,
        version: manifest.version,
        interactionCount: manifest.interactions.length,
        gestureCount: manifest.supportedGestures.length,
        shortcutCount: manifest.supportedShortcuts.length,
      })),
      interactions: [...interactionIndex.keys()],
    };
  }

  return {
    register,
    unregister,
    get,
    list,
    resolve,
    registerHandler,
    execute,
    snapshot,
  };
}

export function createDefaultInteractionRegistry() {
  return createInteractionRegistry();
}

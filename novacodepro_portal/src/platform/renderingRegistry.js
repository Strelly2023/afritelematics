import { createProductRenderingManifest } from "./renderingManifest.js";

function toString(value, fallback = "") {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

export function createRenderingRegistry() {
  const manifests = new Map();
  const screenIndex = new Map();
  const componentIndex = new Map();
  const interactionIndex = new Map();

  function register(manifest) {
    const normalized = createProductRenderingManifest(manifest);
    if (manifests.has(normalized.productCode)) {
      throw new Error(`Product rendering manifest already registered for ${normalized.productCode}.`);
    }

    for (const screen of normalized.screens) {
      if (!screen.screenId) {
        throw new Error("Rendering manifest contains a screen without screenId.");
      }
      if (screenIndex.has(screen.screenId)) {
        throw new Error(`Screen conflict detected for ${screen.screenId}.`);
      }
      screenIndex.set(screen.screenId, normalized.productCode);
    }

    for (const component of normalized.components) {
      if (!component.componentId) {
        throw new Error("Rendering manifest contains a component without componentId.");
      }
      if (componentIndex.has(component.componentId)) {
        throw new Error(`Component conflict detected for ${component.componentId}.`);
      }
      componentIndex.set(component.componentId, normalized.productCode);
    }

    for (const interaction of normalized.interactions) {
      if (!interaction.interactionId) {
        throw new Error("Rendering manifest contains an interaction without interactionId.");
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
    for (const [key, owner] of [...screenIndex.entries()]) {
      if (owner === normalizedProductCode) {
        screenIndex.delete(key);
      }
    }
    for (const [key, owner] of [...componentIndex.entries()]) {
      if (owner === normalizedProductCode) {
        componentIndex.delete(key);
      }
    }
    for (const [key, owner] of [...interactionIndex.entries()]) {
      if (owner === normalizedProductCode) {
        interactionIndex.delete(key);
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

  function getScreen(screenId) {
    const normalizedScreenId = toString(screenId);
    for (const manifest of manifests.values()) {
      const screen = manifest.screens.find((item) => item.screenId === normalizedScreenId);
      if (screen) {
        return screen;
      }
    }
    return null;
  }

  function listProductScreens(productCode) {
    return get(productCode)?.screens || [];
  }

  function listInteractions(productCode) {
    return get(productCode)?.interactions || [];
  }

  function snapshot() {
    return {
      productCount: manifests.size,
      products: list().map((manifest) => ({
        productCode: manifest.productCode,
        version: manifest.version,
        screenCount: manifest.screens.length,
        componentCount: manifest.components.length,
        interactionCount: manifest.interactions.length,
        layoutCount: manifest.layouts.length,
        viewportProfiles: manifest.supportedViewports,
        inputModes: manifest.supportedInputModes,
      })),
      screens: [...screenIndex.keys()],
      components: [...componentIndex.keys()],
      interactions: [...interactionIndex.keys()],
    };
  }

  return {
    register,
    unregister,
    get,
    list,
    getScreen,
    listProductScreens,
    listInteractions,
    snapshot,
  };
}

export function createDefaultRenderingRegistry() {
  return createRenderingRegistry();
}


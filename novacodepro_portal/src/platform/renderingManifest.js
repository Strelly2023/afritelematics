const SHARED_LAYOUTS = new Set([
  "default",
  "full-width",
  "dashboard",
  "workspace",
  "map",
  "split-pane",
  "three-column",
  "detail",
  "wizard",
  "command-centre",
  "mobile-stack",
  "immersive",
  "shared",
  "solution",
]);

const SHARED_VIEWPORTS = new Set([
  "mobile-small",
  "mobile",
  "tablet",
  "desktop",
  "desktop-wide",
  "wall-display",
]);

const SHARED_INPUT_MODES = new Set([
  "mouse",
  "touch",
  "keyboard",
  "stylus",
  "screen-reader",
  "voice",
]);

function toString(value, fallback = "") {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

function asArray(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }
  return [];
}

function normalizeList(value, fallback = []) {
  const items = asArray(value);
  return items.length ? items.map((item) => toString(item)) : fallback.slice();
}

function normalizeScreen(screen, fallbackProductCode) {
  const viewportProfiles = normalizeList(screen.viewportProfiles || screen.supportedViewports || [], [
    "desktop",
  ]);
  for (const profile of viewportProfiles) {
    if (!SHARED_VIEWPORTS.has(profile)) {
      throw new Error(`Unsupported viewport profile "${profile}".`);
    }
  }
  const layout = toString(screen.layout || "shared");
  if (!SHARED_LAYOUTS.has(layout)) {
    throw new Error(`Unsupported layout "${layout}".`);
  }
  return {
    screenId: toString(screen.screenId),
    productCode: toString(screen.productCode || fallbackProductCode),
    routeId: toString(screen.routeId),
    componentId: toString(screen.componentId || ""),
    layout,
    title: toString(screen.title || screen.label || screen.screenId),
    requiredPermissions: normalizeList(screen.requiredPermissions || []),
    featureFlag: toString(screen.featureFlag || ""),
    loadingState: toString(screen.loadingState || "skeleton"),
    emptyState: toString(screen.emptyState || ""),
    errorBoundary: toString(screen.errorBoundary || "product-route"),
    viewportProfiles,
    interactionProfile: toString(screen.interactionProfile || "default"),
    telemetryName: toString(screen.telemetryName || screen.screenId || "screen"),
  };
}

function normalizeComponent(component, fallbackProductCode) {
  return {
    componentId: toString(component.componentId),
    productCode: toString(component.productCode || fallbackProductCode),
    category: toString(component.category || "product"),
    accessibilityLevel: toString(component.accessibilityLevel || "WCAG 2.2 AA"),
    supportedThemes: normalizeList(component.supportedThemes || ["light", "dark"]),
    supportedViewports: normalizeList(component.supportedViewports || ["desktop"]),
    featureFlag: toString(component.featureFlag || ""),
    reusableAcrossProducts: Boolean(component.reusableAcrossProducts),
  };
}

function normalizeInteraction(interaction, fallbackProductCode) {
  return {
    interactionId: toString(interaction.interactionId),
    productCode: toString(interaction.productCode || fallbackProductCode),
    type: toString(interaction.type || "CLICK").toUpperCase(),
    trigger: toString(interaction.trigger || ""),
    target: toString(interaction.target || ""),
    requiredPermissions: normalizeList(interaction.requiredPermissions || []),
    featureFlag: toString(interaction.featureFlag || ""),
    confirmationPolicy: toString(interaction.confirmationPolicy || ""),
    undoPolicy: toString(interaction.undoPolicy || ""),
    accessibilityAnnouncement: toString(interaction.accessibilityAnnouncement || ""),
    telemetryEvent: toString(interaction.telemetryEvent || interaction.interactionId || "interaction"),
  };
}

function normalizeLayout(layout, fallbackProductCode) {
  return {
    layoutId: toString(layout.layoutId),
    productCode: toString(layout.productCode || fallbackProductCode),
    regions: asArray(layout.regions || []).map((region) => ({
      regionId: toString(region.regionId || region.id || region.name),
      allowedProducts: normalizeList(region.allowedProducts || []),
      multiple: Boolean(region.multiple),
      priority: Number.isFinite(region.priority) ? Number(region.priority) : 0,
    })),
    responsiveRules: asArray(layout.responsiveRules || []),
    accessibilityRules: asArray(layout.accessibilityRules || []),
  };
}

export function createProductRenderingManifest(manifest) {
  if (!manifest || typeof manifest !== "object") {
    throw new Error("Product rendering manifest must be an object.");
  }
  const productCode = toString(manifest.productCode);
  if (!productCode) {
    throw new Error("Product rendering manifest missing productCode.");
  }
  const screens = asArray(manifest.screens || []).map((screen) => normalizeScreen(screen, productCode));
  const layouts = asArray(manifest.layouts || []).map((layout) => normalizeLayout(layout, productCode));
  const components = asArray(manifest.components || []).map((component) => normalizeComponent(component, productCode));
  const interactions = asArray(manifest.interactions || []).map((interaction) =>
    normalizeInteraction(interaction, productCode),
  );
  const commands = asArray(manifest.commands || []).map((command) => ({
    commandId: toString(command.commandId || command.id),
    productCode,
    label: toString(command.label || command.commandId || command.id),
    description: toString(command.description || ""),
  }));

  for (const inputMode of asArray(manifest.supportedInputModes || ["mouse", "keyboard"])) {
    const normalized = toString(inputMode);
    if (!SHARED_INPUT_MODES.has(normalized)) {
      throw new Error(`Unsupported input mode "${normalized}".`);
    }
  }

  return {
    productCode,
    version: toString(manifest.version || "1"),
    screens,
    layouts,
    components,
    interactions,
    commands,
    requiredPermissions: normalizeList(manifest.requiredPermissions || []),
    featureFlags: normalizeList(manifest.featureFlags || []),
    supportedViewports: normalizeList(manifest.supportedViewports || ["desktop"]),
    supportedInputModes: normalizeList(manifest.supportedInputModes || ["mouse", "keyboard"]),
    accessibilityProfile: toString(manifest.accessibilityProfile || "WCAG 2.2 AA"),
    telemetryNamespace: toString(manifest.telemetryNamespace || productCode),
  };
}

export const PRODUCT_RENDERING_LAYOUTS = [...SHARED_LAYOUTS];
export const PRODUCT_RENDERING_VIEWPORTS = [...SHARED_VIEWPORTS];
export const PRODUCT_RENDERING_INPUT_MODES = [...SHARED_INPUT_MODES];

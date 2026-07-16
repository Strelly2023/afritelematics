const SHARED_INTERACTION_TYPES = new Set([
  "CLICK",
  "SELECT",
  "SUBMIT",
  "OPEN",
  "CLOSE",
  "NAVIGATE",
  "DRAG",
  "DROP",
  "SWIPE",
  "ZOOM",
  "PAN",
  "COPY",
  "PASTE",
  "UPLOAD",
  "DOWNLOAD",
  "CONFIRM",
  "CANCEL",
  "RETRY",
  "UNDO",
  "REDO",
  "SHORTCUT",
]);

function toString(value, fallback = "") {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

function asArray(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

export function createProductInteractionManifest(manifest) {
  if (!manifest || typeof manifest !== "object") {
    throw new Error("Product interaction manifest must be an object.");
  }
  const productCode = toString(manifest.productCode);
  if (!productCode) {
    throw new Error("Product interaction manifest missing productCode.");
  }
  const interactions = asArray(manifest.interactions || []).map((interaction) => {
    const type = toString(interaction.type || "CLICK").toUpperCase();
    if (!SHARED_INTERACTION_TYPES.has(type)) {
      throw new Error(`Unsupported interaction type "${type}".`);
    }
    return {
      interactionId: toString(interaction.interactionId),
      productCode: toString(interaction.productCode || productCode),
      type,
      trigger: toString(interaction.trigger || ""),
      target: toString(interaction.target || ""),
      requiredPermissions: asArray(interaction.requiredPermissions || []).map((item) => toString(item)),
      featureFlag: toString(interaction.featureFlag || ""),
      confirmationPolicy: toString(interaction.confirmationPolicy || ""),
      undoPolicy: toString(interaction.undoPolicy || ""),
      accessibilityAnnouncement: toString(interaction.accessibilityAnnouncement || ""),
      telemetryEvent: toString(interaction.telemetryEvent || interaction.interactionId || "interaction"),
    };
  });

  return {
    productCode,
    version: toString(manifest.version || "1"),
    interactions,
    supportedGestures: asArray(manifest.supportedGestures || []).map((item) => toString(item)),
    supportedShortcuts: asArray(manifest.supportedShortcuts || []).map((item) => toString(item)),
    accessibilityProfile: toString(manifest.accessibilityProfile || "WCAG 2.2 AA"),
    telemetryNamespace: toString(manifest.telemetryNamespace || productCode),
  };
}

export const PRODUCT_INTERACTION_TYPES = [...SHARED_INTERACTION_TYPES];

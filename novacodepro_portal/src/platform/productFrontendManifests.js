import { createProductFrontendManifest } from "./productFrontendRegistry.js";
import { createProductInteractionManifest } from "./interactionManifest.js";
import { createProductRenderingManifest } from "./renderingManifest.js";
import { ROUTES } from "./routes.js";

export const NOVACODEPRO_FRONTEND_MANIFEST = createProductFrontendManifest({
  productCode: "novacodepro",
  version: "2026.07.0",
  displayName: "NovaCodePro Portal",
  routePrefix: "/novacodepro",
  navigationItems: [
    {
      id: "novacodepro-dashboard",
      label: "Dashboard",
      path: ROUTES.dashboard,
      permission: "novacodepro:workspace:view",
    },
    {
      id: "novacodepro-solutions",
      label: "Solution Engineering",
      path: ROUTES.solutionRoot,
      permission: "novacodepro:solutions:view",
    },
  ],
  routes: [
    {
      routeId: "novacodepro.dashboard",
      productCode: "novacodepro",
      path: ROUTES.dashboard,
      title: "Dashboard",
      audience: "EMPLOYEE",
      layout: "shared",
      featureFlag: "novacodepro.enabled",
      requiredPermissions: ["novacodepro:workspace:view"],
    },
  ],
  requiredPermissions: ["novacodepro:workspace:view", "novacodepro:solutions:view"],
  featureFlags: ["novacodepro.enabled", "novacodepro.solution-engineering.enabled"],
  supportedLocales: ["en-AU", "en"],
  branding: {
    productName: "NovaCodePro",
    icon: "novacodepro",
    accentToken: "product.engineering",
    heroVariant: "enterprise-ai",
  },
  apiDependencies: [
    {
      name: "novacodepro-api",
      basePath: "/v1/novacodepro",
      version: "v1",
    },
    {
      name: "solution-engineering-api",
      basePath: "/v1/solution-engineering",
      version: "v1",
    },
  ],
  telemetryNamespace: "novacodepro",
  apps: ["employee-portal", "customer-portal"],
  configurationSchema: {
    version: 1,
    fields: [
      { name: "aiAssistantEnabled", type: "boolean", default: true },
      { name: "voiceInputEnabled", type: "boolean", default: true },
      { name: "repositoryImportEnabled", type: "boolean", default: true },
      { name: "automationEnabled", type: "boolean", default: true },
      { name: "approvalWorkspaceEnabled", type: "boolean", default: true },
    ],
  },
});

export const NOVACODEPRO_RENDERING_MANIFEST = createProductRenderingManifest({
  productCode: "novacodepro",
  version: "2026.07.0",
  supportedViewports: ["mobile", "tablet", "desktop", "desktop-wide"],
  supportedInputModes: ["mouse", "touch", "keyboard", "voice", "screen-reader"],
  telemetryNamespace: "novacodepro",
  screens: [
    {
      screenId: "novacodepro.dashboard",
      productCode: "novacodepro",
      routeId: "novacodepro.dashboard",
      layout: "dashboard",
      title: "NovaCodePro Dashboard",
      requiredPermissions: ["novacodepro:workspace:view"],
      featureFlag: "novacodepro.enabled",
      loadingState: "full-screen startup",
      errorBoundary: "product-route",
      viewportProfiles: ["mobile", "tablet", "desktop", "desktop-wide"],
      interactionProfile: "workspace-shell",
      telemetryName: "novacodepro_dashboard",
    },
    {
      screenId: "solution-engineering.root",
      productCode: "solution-engineering",
      routeId: "solution-engineering.root",
      layout: "workspace",
      title: "Solution Engineering",
      requiredPermissions: ["solution-engineering:project:view"],
      featureFlag: "solution-engineering.enabled",
      loadingState: "skeleton",
      errorBoundary: "product-route",
      viewportProfiles: ["desktop", "desktop-wide"],
      interactionProfile: "solution-workspace",
      telemetryName: "solution_engineering_root",
    },
    {
      screenId: "solution-engineering.projects",
      productCode: "solution-engineering",
      routeId: "solution-engineering.projects",
      layout: "workspace",
      title: "Solution Engineering Projects",
      requiredPermissions: ["solution-engineering:project:view"],
      featureFlag: "solution-engineering.enabled",
      loadingState: "table-placeholder",
      errorBoundary: "product-route",
      viewportProfiles: ["desktop", "desktop-wide"],
      interactionProfile: "project-browser",
      telemetryName: "solution_engineering_projects",
    },
  ],
  layouts: [
    {
      layoutId: "dashboard",
      regions: [
        { regionId: "header", allowedProducts: ["novacodepro"], multiple: false, priority: 1 },
        { regionId: "main", allowedProducts: ["novacodepro"], multiple: false, priority: 2 },
        { regionId: "sidebar", allowedProducts: ["novacodepro"], multiple: true, priority: 3 },
      ],
      responsiveRules: ["desktop:three-column", "mobile:stacked"],
      accessibilityRules: ["skip-link", "focus-management"],
    },
    {
      layoutId: "workspace",
      regions: [
        { regionId: "header", allowedProducts: ["solution-engineering"], multiple: false, priority: 1 },
        { regionId: "workspace", allowedProducts: ["solution-engineering"], multiple: false, priority: 2 },
        { regionId: "context", allowedProducts: ["solution-engineering"], multiple: true, priority: 3 },
      ],
      responsiveRules: ["desktop:split-pane", "tablet:drawer"],
      accessibilityRules: ["skip-link", "dialog-focus-trap"],
    },
  ],
  components: [
    {
      componentId: "novacodepro.universal-ai-workspace",
      productCode: "novacodepro",
      category: "workspace",
      accessibilityLevel: "WCAG 2.2 AA",
      supportedThemes: ["light", "dark", "high-contrast"],
      supportedViewports: ["mobile", "tablet", "desktop", "desktop-wide"],
      reusableAcrossProducts: true,
    },
    {
      componentId: "solution-engineering.portal",
      productCode: "solution-engineering",
      category: "workspace",
      accessibilityLevel: "WCAG 2.2 AA",
      supportedThemes: ["light", "dark", "high-contrast"],
      supportedViewports: ["desktop", "desktop-wide"],
      reusableAcrossProducts: false,
    },
  ],
  interactions: [
    {
      interactionId: "novacodepro.ai.ask",
      productCode: "novacodepro",
      type: "SUBMIT",
      trigger: "composer send",
      target: "universal ai workspace",
      requiredPermissions: ["novacodepro:workspace:view"],
      featureFlag: "novacodepro.enabled",
      confirmationPolicy: "high-risk-requests",
      undoPolicy: "timed-undo",
      accessibilityAnnouncement: "Request sent to NovaAI.",
      telemetryEvent: "novacodepro_ai_request_submitted",
    },
    {
      interactionId: "novacodepro.workspace.open",
      productCode: "novacodepro",
      type: "NAVIGATE",
      trigger: "role switch",
      target: "role dashboard",
      requiredPermissions: ["novacodepro:workspace:view"],
      featureFlag: "novacodepro.enabled",
      accessibilityAnnouncement: "Workspace opened.",
      telemetryEvent: "novacodepro_workspace_opened",
    },
    {
      interactionId: "solution-engineering.request",
      productCode: "solution-engineering",
      type: "SUBMIT",
      trigger: "project submit",
      target: "solution engineering workspace",
      requiredPermissions: ["solution-engineering:project:view"],
      featureFlag: "solution-engineering.enabled",
      accessibilityAnnouncement: "Solution engineering request submitted.",
      telemetryEvent: "solution_engineering_request_submitted",
    },
  ],
  commands: [
    { commandId: "novacodepro.ask-ai", label: "Ask NovaAI", description: "Open the universal AI workspace composer." },
    { commandId: "solution-engineering.open", label: "Open Solution Engineering", description: "Open the solution engineering workspace." },
  ],
});

export const NOVACODEPRO_INTERACTION_MANIFEST = createProductInteractionManifest({
  productCode: "novacodepro",
  version: "2026.07.0",
  supportedGestures: ["pan", "zoom", "drag", "drop", "swipe"],
  supportedShortcuts: ["Meta+K", "Escape", "Enter", "Space"],
  telemetryNamespace: "novacodepro",
  interactions: NOVACODEPRO_RENDERING_MANIFEST.interactions,
});

export const SOLUTION_ENGINEERING_FRONTEND_MANIFEST = createProductFrontendManifest({
  productCode: "solution-engineering",
  version: "2026.07.0",
  displayName: "Solution Engineering",
  routePrefix: "/novacodepro/solutions",
  navigationItems: [
    {
      id: "solutions-overview",
      label: "Overview",
      path: ROUTES.solutionRoot,
      permission: "solution-engineering:project:view",
    },
    {
      id: "solutions-projects",
      label: "Projects",
      path: ROUTES.solutionProjects,
      permission: "solution-engineering:project:view",
    },
  ],
  routes: [
    {
      routeId: "solution-engineering.root",
      productCode: "solution-engineering",
      path: ROUTES.solutionRoot,
      title: "Solution Engineering",
      audience: "EMPLOYEE",
      layout: "solution",
      featureFlag: "solution-engineering.enabled",
      requiredPermissions: ["solution-engineering:project:view"],
    },
    {
      routeId: "solution-engineering.projects",
      productCode: "solution-engineering",
      path: ROUTES.solutionProjects,
      title: "Projects",
      audience: "EMPLOYEE",
      layout: "solution",
      featureFlag: "solution-engineering.enabled",
      requiredPermissions: ["solution-engineering:project:view"],
    },
  ],
  requiredPermissions: ["solution-engineering:project:view"],
  featureFlags: ["solution-engineering.enabled"],
  supportedLocales: ["en-AU", "en"],
  branding: {
    productName: "Solution Engineering",
    icon: "solution-engineering",
    accentToken: "product.ai",
    heroVariant: "solution-fabric",
  },
  apiDependencies: [
    {
      name: "solution-engineering-api",
      basePath: "/v1/solution-engineering",
      version: "v1",
    },
  ],
  telemetryNamespace: "solution-engineering",
  apps: ["employee-portal"],
  configurationSchema: {
    version: 1,
    fields: [
      { name: "workspaceEnabled", type: "boolean", default: true },
      { name: "approvalWorkspaceEnabled", type: "boolean", default: true },
      { name: "evidenceWorkspaceEnabled", type: "boolean", default: true },
    ],
  },
});

export function registerDefaultFrontendManifests(registry) {
  registry.register(NOVACODEPRO_FRONTEND_MANIFEST);
  registry.register(SOLUTION_ENGINEERING_FRONTEND_MANIFEST);
  return registry;
}

export function registerDefaultRenderingManifests(registry) {
  registry.register(NOVACODEPRO_RENDERING_MANIFEST);
  return registry;
}

export function registerDefaultInteractionManifests(registry) {
  registry.register(NOVACODEPRO_INTERACTION_MANIFEST);
  return registry;
}

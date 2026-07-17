import registry from "../../../contracts/app-registry.json" with { type: "json" };

export type AppRegistryStatus = "active" | "preview" | "disabled";

export interface AppRegistryItem {
  id: string;
  name: string;
  route: string;
  icon: string;
  requiredPermissions: string[];
  featureFlag: string;
  status: AppRegistryStatus;
  domain: string;
  description: string;
  order: number;
}

export interface AppRegistryDocument {
  contractVersion: number;
  platform: string;
  apps: AppRegistryItem[];
}

export const NOVACODEPRO_APP_REGISTRY: AppRegistryDocument = registry as AppRegistryDocument;

export function listNovaCodeProApps(): AppRegistryItem[] {
  return [...NOVACODEPRO_APP_REGISTRY.apps].sort((left, right) => left.order - right.order);
}

export function getNovaCodeProApp(appId: string): AppRegistryItem | null {
  return listNovaCodeProApps().find((app) => app.id === appId) ?? null;
}

export function buildNovaCodeProAppLauncher(permissions: Iterable<string> = []): Array<AppRegistryItem & { accessible: boolean }> {
  const allowed = new Set(Array.from(permissions, (value) => String(value)));
  return listNovaCodeProApps().map((app) => ({
    ...app,
    accessible: app.status !== "disabled" && (app.requiredPermissions.length === 0 || app.requiredPermissions.every((permission) => allowed.has(permission))),
  }));
}

export function findNovaCodeProAppByPath(pathname: string): AppRegistryItem | null {
  const normalized = String(pathname || "/").trim() || "/";
  const normalizedPath = normalized.startsWith("/") ? normalized.replace(/\/+$/, "") || "/" : `/${normalized}`.replace(/\/+$/, "") || "/";
  const matches = listNovaCodeProApps()
    .filter((app) => normalizedPath === app.route || normalizedPath.startsWith(`${app.route}/`))
    .sort((left, right) => right.route.length - left.route.length);
  return matches[0] ?? null;
}

export function parseNovaCodeProRoute(pathname: string): { path: string; appId: string; section: string; subRoute: string } | null {
  const normalized = String(pathname || "/").trim() || "/";
  const normalizedPath = normalized.startsWith("/") ? normalized.replace(/\/+$/, "") || "/" : `/${normalized}`.replace(/\/+$/, "") || "/";
  if (!normalizedPath.startsWith("/novacodepro")) {
    return null;
  }
  const app = findNovaCodeProAppByPath(normalizedPath);
  if (!app) {
    return null;
  }
  const remainder = normalizedPath === app.route ? "" : normalizedPath.slice(app.route.length);
  return {
    path: normalizedPath,
    appId: app.id,
    section: app.id,
    subRoute: remainder || "/",
  };
}

export default NOVACODEPRO_APP_REGISTRY;

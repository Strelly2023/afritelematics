import registry from "../../../contracts/app-registry.json" with { type: "json" };

import { ROUTES, appPath } from "./routes.js";

function normalizePath(pathname) {
  const value = typeof pathname === "string" && pathname.trim() ? pathname.trim() : "/";
  if (!value.startsWith("/")) {
    return `/${value}`;
  }
  return value === "/" ? "/" : value.replace(/\/+$/, "") || "/";
}

export const NOVACODEPRO_APP_REGISTRY = registry;

export function listNovaCodeProApps() {
  return [...(NOVACODEPRO_APP_REGISTRY.apps || [])].sort((left, right) => left.order - right.order);
}

export function getNovaCodeProApp(appId) {
  return listNovaCodeProApps().find((app) => app.id === appId) || null;
}

export function buildNovaCodeProAppLauncher(permissions = []) {
  const allowed = new Set(Array.from(permissions, (value) => String(value)));
  return listNovaCodeProApps().map((app) => ({
    ...app,
    accessible: app.status !== "disabled" && (app.requiredPermissions.length === 0 || app.requiredPermissions.every((permission) => allowed.has(permission))),
  }));
}

export function isNovaCodeProRouteAccessible(pathname, permissions = []) {
  const route = parseNovaCodeProRoute(pathname);
  if (!route) {
    return true;
  }
  const app = buildNovaCodeProAppLauncher(permissions).find((item) => item.id === route.appId);
  return Boolean(app?.accessible ?? false);
}

export function findNovaCodeProAppByPath(pathname) {
  const normalized = normalizePath(pathname);
  const matches = listNovaCodeProApps()
    .filter((app) => normalized === app.route || normalized.startsWith(`${app.route}/`))
    .sort((left, right) => right.route.length - left.route.length);
  return matches[0] || null;
}

export function parseNovaCodeProRoute(pathname) {
  const normalized = normalizePath(pathname);
  if (!normalized.startsWith("/novacodepro")) {
    return null;
  }
  const app = findNovaCodeProAppByPath(normalized);
  if (!app) {
    return null;
  }
  const remainder = normalized === app.route ? "" : normalized.slice(app.route.length);
  return {
    path: normalized,
    appId: app.id,
    section: app.id,
    subRoute: remainder || "/",
  };
}

export function isNovaCodeProRoute(pathname) {
  return normalizePath(pathname).startsWith("/novacodepro");
}

export function novacodeproAppPath(pathname) {
  const normalized = normalizePath(pathname);
  return normalized.startsWith("/novacodepro") ? normalized : appPath(normalized);
}

export function buildNovaCodeProWorkspaceRoute(appId, subRoute = "") {
  const app = getNovaCodeProApp(appId);
  if (!app) {
    return ROUTES.workspaceRoot;
  }
  if (!subRoute) {
    return app.route;
  }
  const normalizedSubRoute = subRoute.startsWith("/") ? subRoute : `/${subRoute}`;
  return `${app.route}${normalizedSubRoute}`;
}

import { resolveWorkspaceSlugFromLoginRole } from "./workspaceRoutes.js";

export const APP_BASE = "/novacodepro";

export function appPath(path = "/") {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (normalized === "/") {
    return `${APP_BASE}/`;
  }
  return `${APP_BASE}${normalized}`;
}

export function appUrl(path = "/", query = {}) {
  const target = appPath(path);
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query || {})) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    params.set(key, String(value));
  }
  const search = params.toString();
  return search ? `${target}?${search}` : target;
}

export const ROUTES = {
  home: appPath("/"),
  login: appPath("/login"),
  dashboard: appPath("/dashboard"),
  logout: appPath("/logout"),
  workspaceRoot: appPath("/workspace"),
  productFactoryRoot: appPath("/product-factory"),
  strategyRoot: appPath("/strategy"),
  projectsRoot: appPath("/projects"),
  requestsRoot: appPath("/requests"),
  aiRoot: appPath("/ai"),
  conversationRoot: appPath("/conversation"),
  architectureRoot: appPath("/architecture"),
  designRoot: appPath("/design"),
  codeRoot: appPath("/code"),
  apisRoot: appPath("/apis"),
  dataRoot: appPath("/data"),
  testingRoot: appPath("/testing"),
  securityRoot: appPath("/security"),
  devopsRoot: appPath("/devops"),
  releasesRoot: appPath("/releases"),
  operationsRoot: appPath("/operations"),
  adminRoot: appPath("/admin"),
  solutionRoot: appPath("/solutions"),
  solutionCustomers: appPath("/solutions/customers"),
  solutionProjects: appPath("/solutions/projects"),
  solutionProject(projectId, section = "dashboard") {
    return appPath(`/solutions/projects/${encodeURIComponent(projectId)}/${section}`);
  },
  roleDashboard(role) {
    const slug = resolveWorkspaceSlugFromLoginRole(role) || "workspace";
    return appPath(`/workspace/${encodeURIComponent(slug)}/dashboard`);
  },
  loginWithReason(reason, returnTo) {
    return appUrl("/login", { reason, returnTo });
  },
};

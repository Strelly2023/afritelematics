import { expect, type Page } from "@playwright/test";

export const backendBaseUrl = process.env.PW_BACKEND_BASE_URL || "http://127.0.0.1:18001";
export const frontendBaseUrl = process.env.PW_FRONTEND_BASE_URL || "http://127.0.0.1:14173";
export const authStorageKey = "novaride.operations.auth_token";
export const runtimeConfig = {
  baseUrl: `${backendBaseUrl}/api/v1/novaride/operations`,
  authBaseUrl: `${backendBaseUrl}/v1`,
  liveMapEnabled: true,
  refundExecutionEnabled: true,
  productionActionsEnabled: true,
};

export const roleMapping: Record<string, string> = {
  PLATFORM_ADMIN: "ADMIN",
  OPERATIONS_TEAM: "OPERATIONS_TEAM",
  CUSTOMER_SUPPORT: "CUSTOMER_SUPPORT",
  SAFETY_OPERATOR: "INCIDENT_RESPONSE_TEAM",
  READ_ONLY_AUDITOR: "READ_ONLY_REVIEWER",
  UNAUTHORIZED_USER: "CUSTOMER",
  CROSS_TENANT_OPERATOR: "ADMIN",
};

export async function signIn(page: Page, semanticRole = "OPERATIONS_TEAM", userId = "ops_browser") {
  const canonicalRole = roleMapping[semanticRole] || semanticRole;
  await page.addInitScript((config) => {
    window.__NOVARIDE_OPERATION_CONFIG__ = config;
  }, runtimeConfig);
  const response = await page.request.post(`${backendBaseUrl}/v1/auth/token`, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    data: {
      user_id: userId,
      role: canonicalRole,
      tenant_id: "novaride-tenant",
      organization_id: "novaride-org",
      region: "AU",
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  await page.addInitScript(
    ([key, token]) => {
      window.localStorage.setItem(key, token);
    },
    [authStorageKey, String((payload as { token: string }).token)],
  );
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Operations workspace" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
  await expect(page.getByText(userId)).toBeVisible();
  return canonicalRole;
}

export async function signInWithSession(page: Page, semanticRole = "OPERATIONS_TEAM", userId = "ops_browser") {
  const canonicalRole = await signIn(page, semanticRole, userId);
  const token = await page.evaluate((key) => window.localStorage.getItem(key) || "", authStorageKey);
  expect(token).toBeTruthy();
  return { canonicalRole, token };
}

export async function createAuthToken(
  page: Page,
  {
    semanticRole = "OPERATIONS_TEAM",
    userId = "ops_browser",
    ttlSeconds,
    authPath = "/v1/auth/token",
  }: {
    semanticRole?: string;
    userId?: string;
    ttlSeconds?: number;
    authPath?: string;
  } = {},
) {
  const canonicalRole = roleMapping[semanticRole] || semanticRole;
  const response = await page.request.post(`${backendBaseUrl}${authPath}`, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    data: {
      user_id: userId,
      role: canonicalRole,
      tenant_id: "novaride-tenant",
      organization_id: "novaride-org",
      region: "AU",
      ...(ttlSeconds != null ? { ttl_seconds: ttlSeconds } : {}),
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  return { canonicalRole, token: String((payload as { token: string }).token) };
}

export function buildBrowserSessionToken({
  userId = "ops_browser",
  semanticRole = "OPERATIONS_TEAM",
  tenantId = "novaride-tenant",
  organizationId = "novaride-org",
  region = "AU",
  expiresInSeconds = 12 * 60 * 60,
}: {
  userId?: string;
  semanticRole?: string;
  tenantId?: string;
  organizationId?: string;
  region?: string;
  expiresInSeconds?: number;
} = {}) {
  const canonicalRole = roleMapping[semanticRole] || semanticRole;
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" }), "utf8").toString("base64url");
  const payload = Buffer.from(
    JSON.stringify({
      sub: userId,
      role: canonicalRole,
      tenant_id: tenantId,
      organization_id: organizationId,
      region,
      exp: Math.floor(Date.now() / 1000) + expiresInSeconds,
    }),
    "utf8",
  ).toString("base64url");
  return `${header}.${payload}.test-signature`;
}

export async function seedBrowserFixture(page: Page, token: string) {
  const response = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/bootstrap`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok()) {
    if (response.status() === 404) {
      return { skipped: true, reason: "bootstrap_route_unavailable" };
    }
    const body = await response.text().catch(() => "");
    throw new Error(`Bootstrap seed failed (${response.status()}): ${body.slice(0, 200)}`);
  }
  return response.json();
}

export async function signInAndSeed(
  page: Page,
  semanticRole = "OPERATIONS_TEAM",
  userId = "ops_browser",
  { waitForOverview = true }: { waitForOverview?: boolean } = {},
) {
  const { canonicalRole, token } = await signInWithSession(page, semanticRole, userId);
  const seed = await seedBrowserFixture(page, token);
  await page.reload();
  if (waitForOverview) {
    await expect(page.getByText("Active trips", { exact: true })).toBeVisible({ timeout: 30_000 });
  }
  return { canonicalRole, token, seed };
}

export async function logout(page: Page) {
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Sign in to the operations workspace" })).toBeVisible();
}

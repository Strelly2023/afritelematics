import { expect, test } from "@playwright/test";
import { backendBaseUrl, roleMapping, runtimeConfig } from "./helpers";

test("cross-tenant tokens remain isolated from another tenant's operations data", async ({ page }) => {
  await page.addInitScript((config) => {
    window.__NOVARIDE_OPERATION_CONFIG__ = config;
  }, runtimeConfig);
  const tokenResponse = await page.request.post(`${backendBaseUrl}/v1/auth/token`, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    data: {
      user_id: "cross_tenant_browser",
      role: roleMapping.CROSS_TENANT_OPERATOR,
      tenant_id: "other-tenant",
      organization_id: "other-org",
      region: "EU",
    },
  });
  expect(tokenResponse.ok()).toBeTruthy();
  const { token } = await tokenResponse.json();
  await page.goto("/");
  await page.evaluate(([key, value]) => {
    window.localStorage.setItem(key, value);
  }, ["novaride.operations.auth_token", token]);
  await page.reload();
  await page.getByRole("button", { name: "Overview" }).click();
  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/incidents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.items).toEqual([]);

  const overview = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/overview`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(overview.ok()).toBeTruthy();
  const overviewJson = await overview.json();
  expect(overviewJson.summary.open_incidents).toBe(0);
  expect(overviewJson.summary.active_trips).toBe(0);
});

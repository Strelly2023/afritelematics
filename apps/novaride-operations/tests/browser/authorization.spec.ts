import { expect, test } from "@playwright/test";
import { backendBaseUrl, roleMapping, runtimeConfig } from "./helpers";

test("wrong role tenant and region are denied by the backend", async ({ page }) => {
  await page.addInitScript((config) => {
    window.__NOVARIDE_OPERATION_CONFIG__ = config;
  }, runtimeConfig);
  const tokenResponse = await page.request.post(`${backendBaseUrl}/auth/token`, {
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
  const response = await page.request.get(`${backendBaseUrl}/v1/novaride/operations/incidents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect([401, 403, 404]).toContain(response.status());
});

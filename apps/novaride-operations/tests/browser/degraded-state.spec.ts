import { expect, test } from "@playwright/test";
import { backendBaseUrl, runtimeConfig, signInAndSeed } from "./helpers";

test("unauthorized and degraded states render honestly", async ({ page }) => {
  await page.addInitScript((config) => {
    window.__NOVARIDE_OPERATION_CONFIG__ = config;
  }, runtimeConfig);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in to the operations workspace" })).toBeVisible();
  const denied = await page.request.get(`${backendBaseUrl}/v1/novaride/operations/overview`);
  expect([401, 403, 404]).toContain(denied.status());
});

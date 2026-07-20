import { expect, test } from "@playwright/test";
import { authStorageKey, buildBrowserSessionToken, logout, runtimeConfig, seedBrowserFixture, signIn, signInAndSeed } from "./helpers";

test("authenticated browser sessions support login logout and re-authentication", async ({ page }) => {
  const { token } = await signInAndSeed(page, "OPERATIONS_TEAM", "ops_browser");
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
  await expect(page.getByText("ops_browser")).toBeVisible();
  await logout(page);
  await expect(page.getByRole("heading", { name: "Sign in to the operations workspace" })).toBeVisible();
  await signIn(page, "PLATFORM_ADMIN", "admin_browser");
  const reauthenticated = await page.evaluate((key) => window.localStorage.getItem(key) || "", authStorageKey);
  expect(reauthenticated).toBeTruthy();
  await seedBrowserFixture(page, token);
});

test("session expiry is handled safely", async ({ page }) => {
  await page.addInitScript((config) => {
    window.__NOVARIDE_OPERATION_CONFIG__ = config;
  }, runtimeConfig);
  const payload = buildBrowserSessionToken({ userId: "ops_browser", semanticRole: "OPERATIONS_TEAM", expiresInSeconds: -60 });
  await page.addInitScript(
    ([key, value]) => {
      window.localStorage.setItem(key, value);
    },
    [authStorageKey, payload.token],
  );
  await page.goto("/");
  await page.waitForTimeout(1500);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Sign in to the operations workspace" })).toBeVisible();
  await expect(page.getByText("Your session expired. Sign in again.")).toBeVisible();
});

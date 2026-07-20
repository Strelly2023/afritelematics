import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("operations overview is live backend-backed data", async ({ page }) => {
  const { token } = await signInAndSeed(page);
  await expect(page.getByRole("heading", { name: "Operations workspace" })).toBeVisible();
  await expect(page.getByText("Authoritative backend state")).toBeVisible();
  await expect(page.getByRole("button", { name: "Overview" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Active trips", { exact: true })).toBeVisible();
  await expect(page.getByText("Online drivers", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dependency health", exact: true })).toBeVisible();
  await expect(page.getByText("Evidence-preserving workflows")).toBeVisible();

  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/overview`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const api = await response.json();
  await expect(page.locator(".metric-card", { hasText: "Active trips" }).getByText(String(api.summary.active_trips), { exact: true })).toBeVisible();
  await expect(page.locator(".metric-card", { hasText: "Online drivers" }).getByText(String(api.summary.drivers_online), { exact: true })).toBeVisible();
  await expect(page.locator(".metric-card", { hasText: "Support cases" }).getByText(String(api.summary.open_support_cases), { exact: true })).toBeVisible();
});

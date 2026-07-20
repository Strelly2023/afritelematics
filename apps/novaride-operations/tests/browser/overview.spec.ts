import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("operations overview is live backend-backed data", async ({ page }) => {
  const { token } = await signInAndSeed(page);
  await expect(page.getByRole("heading", { name: "Operations workspace" })).toBeVisible();
  await expect(page.getByText("Authoritative backend state")).toBeVisible();
  await expect(page.getByRole("button", { name: "Overview" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("operations-loaded")).toBeVisible();
  await expect(page.getByTestId("active-trips-value")).toBeVisible();
  await expect(page.getByTestId("online-drivers-value")).toBeVisible();
  await expect(page.locator('[data-testid="dependency-health-section"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="dependency-health-section"]').getByRole("heading", { name: "Dependency health", exact: true })).toBeVisible();
  await expect(page.getByText("Evidence-preserving workflows")).toBeVisible();

  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/overview`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const api = await response.json();
  await expect(page.getByTestId("active-trips-value")).toHaveText(String(api.summary.active_trips));
  await expect(page.getByTestId("online-drivers-value")).toHaveText(String(api.summary.drivers_online));
  await expect(page.getByTestId("support-cases-value")).toHaveText(String(api.summary.open_support_cases));
});

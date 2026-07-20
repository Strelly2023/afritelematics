import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("support workflow supports governed creation assignment and resolution", async ({ page }) => {
  const { token } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Support" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Support");
  await page.getByLabel("Case type").fill("browser_case");
  await page.getByLabel("Trip ID").fill("trip_browser_1");
  await page.getByLabel("Payment ID").fill("payment_browser_1");
  await page.getByRole("button", { name: "Create support case" }).click();
  await expect(page.getByText("browser_case")).toBeVisible();

  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/support/cases?trip_id=trip_browser_1`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.items.some((item: { trip_id?: string }) => item.trip_id === "trip_browser_1")).toBeTruthy();

  const card = page.locator(".record-card", { hasText: "browser_case" }).first();
  await card.getByRole("button", { name: "Assign" }).click();
  await card.getByRole("button", { name: "Resolve" }).click();
  await expect(card).toContainText("resolved");
});

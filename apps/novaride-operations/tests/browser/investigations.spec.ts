import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("payment investigations can be opened and reviewed", async ({ page }) => {
  const { token } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Payment investigations" }).click();
  await expect(page.getByRole("heading", { name: "Payment investigations", exact: true })).toBeVisible();
  await expect(page.locator(".record-card").first()).toContainText("payment_browser_1");
  await page.getByLabel("Payment ID").fill("payment_browser_1");
  await page.getByLabel("Reason").fill("Repeated payment capture review");
  await page.getByRole("button", { name: "Open investigation" }).click();
  await expect(page.getByText("payment_browser_1")).toBeVisible();

  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/payments/investigations`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.items.some((item: { payment_id?: string }) => item.payment_id === "payment_browser_1")).toBeTruthy();
});

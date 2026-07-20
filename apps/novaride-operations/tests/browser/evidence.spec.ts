import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("evidence and audit views expose scoped integrity metadata", async ({ page }) => {
  const { token } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Evidence" }).click();
  await expect(page.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();
  await expect(page.locator("#operations-content .section-heading").getByText("Evidence search, lifecycle, integrity, and export controls.", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: /evidence_/ }).first()).toBeVisible();

  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/evidence`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.items.length).toBeGreaterThan(0);
  const first = payload.items[0];
  const card = page.locator(".record-card", { hasText: first.evidence_id }).first();
  await expect(card).toBeVisible();
  await expect(card.getByText(first.correlation_id, { exact: true })).toBeVisible();
});

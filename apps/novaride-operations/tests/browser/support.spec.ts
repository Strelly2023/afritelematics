import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("support workflow supports governed creation assignment and resolution", async ({ page }) => {
  const runId = test.info().testId.replace(/[^a-zA-Z0-9]/g, "-");
  const { token, seed } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Support" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Support");
  await page.getByLabel("Case type").fill(`browser_case_${runId}`);
  await page.getByLabel("Trip ID").fill(seed.trip_ids[0]);
  await page.getByLabel("Payment ID").fill(`payment_browser_${runId}`);
  await page.getByRole("button", { name: "Create support case" }).click();
  await expect(page.getByText(`browser_case_${runId}`)).toBeVisible();

  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/support/cases?trip_id=${seed.trip_ids[0]}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.items.some((item: { trip_id?: string }) => item.trip_id === seed.trip_ids[0])).toBeTruthy();

  const card = page.locator(".record-card", { hasText: `browser_case_${runId}` }).first();
  await card.getByRole("button", { name: "Assign" }).click();
  await card.getByRole("button", { name: "Resolve" }).click();
  await expect(card).toContainText("resolved");
});

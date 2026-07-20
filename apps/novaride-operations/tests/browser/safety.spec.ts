import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("safety cases support assignment escalation and evidence access", async ({ page }) => {
  const { token } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Safety" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Safety");
  const card = page.locator(".record-card", { hasText: "safety_browser_1" });
  await expect(card).toContainText("triaged");
  await expect(card).toContainText("trip_browser_1");
  await card.getByRole("button", { name: "Assign" }).click();
  await expect(card).toContainText("assigned");
  await card.getByRole("button", { name: "Escalate" }).click();
  await expect(card).toContainText("escalated");

  const evidence = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/safety/cases/safety_browser_1/evidence`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(evidence.ok()).toBeTruthy();
  const evidenceJson = await evidence.json();
  expect(evidenceJson.items.length).toBeGreaterThan(0);
});

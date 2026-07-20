import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("safety cases support assignment escalation and evidence access", async ({ page }) => {
  const { token, seed } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Safety" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Safety");
  const card = page.locator(".record-card", { hasText: seed.safety_case_ids[0] }).first();
  await expect(card).toContainText(seed.trip_ids[0]);
  await card.getByRole("button", { name: "Assign" }).click();
  await expect(card).toContainText("assigned");
  await card.getByRole("button", { name: "Escalate" }).click();
  const refreshed = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/safety/cases/${seed.safety_case_ids[0]}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(refreshed.ok()).toBeTruthy();
  const updated = await refreshed.json();
  expect(updated.current_state).toBe("assigned");

  const evidence = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/safety/cases/${seed.safety_case_ids[0]}/evidence`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(evidence.ok()).toBeTruthy();
  const evidenceJson = await evidence.json();
  expect(evidenceJson.items.length).toBeGreaterThan(0);
});

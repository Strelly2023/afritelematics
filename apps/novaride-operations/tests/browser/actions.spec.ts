import { expect, test } from "@playwright/test";
import { backendBaseUrl, signIn, signInAndSeed, logout } from "./helpers";

test("governed operational actions require evaluation approval execution and verification", async ({ page }) => {
  const runId = test.info().testId.replace(/[^a-zA-Z0-9]/g, "-");
  const { token, seed } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Actions" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Actions");
  await page.getByLabel("Action type").fill("manual_dispatch");
  await page.getByLabel("Target").fill(seed.trip_ids[0]);
  await page.getByLabel("Reason").fill(`Browser certification governed action ${runId}`);
  await page.getByRole("button", { name: "Request action" }).click();

  const actionList = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/actions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(actionList.ok()).toBeTruthy();
  const actionJson = await actionList.json();
  const created = actionJson.items.find((item: { target_id?: string; reason?: string }) => item.target_id === seed.trip_ids[0] && item.reason === `Browser certification governed action ${runId}`);
  expect(created).toBeTruthy();
  const requestedCard = page.locator(".record-card", { hasText: created.action_id }).first();
  await expect(requestedCard).toBeVisible();

  const selfApproval = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/actions/${created.action_id}/approve`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    data: { approval_reference: "same-actor" },
  });
  expect(selfApproval.status()).toBe(403);

  await logout(page);
  await signIn(page, "PLATFORM_ADMIN", "admin_browser");
  await page.getByRole("button", { name: "Actions" }).click();
  const card = page.locator(".record-card", { hasText: created.action_id }).first();
  await card.getByRole("button", { name: "Evaluate" }).click();
  await expect(card).toContainText("approval_pending");
  await card.getByRole("button", { name: "Approve" }).click();
  await expect(card).toContainText("approved");
  await card.getByRole("button", { name: "Execute" }).click();
  await expect(card).toContainText("executing");
  await card.getByRole("button", { name: "Verify" }).click();
  await expect(card).toContainText("verified");

  const evidence = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/actions/${created.action_id}/evidence`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(evidence.ok()).toBeTruthy();
  const evidenceJson = await evidence.json();
  expect(evidenceJson.items.length).toBeGreaterThan(0);
});

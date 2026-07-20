import { expect, test } from "@playwright/test";
import { backendBaseUrl, signIn, signInAndSeed, logout } from "./helpers";

test("refund governance enforces dual control and execution verification", async ({ page }) => {
  const runId = test.info().testId.replace(/[^a-zA-Z0-9]/g, "-");
  const { token, seed } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Refunds" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Refunds");

  const payload = {
    amount: "75.00",
    currency: "AUD",
    payment_id: `payment_browser_${runId}`,
    trip_id: seed.trip_ids[0],
    support_case_id: seed.support_case_ids[0],
    reason: `Browser certification refund ${runId}`,
  };
  const idempotencyKey = `browser-refund-certification-${runId}`;
  const created = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/refunds`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    data: payload,
  });
  expect(created.ok()).toBeTruthy();
  const createdJson = await created.json();

  const repeated = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/refunds`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    data: payload,
  });
  expect(repeated.ok()).toBeTruthy();
  const repeatedJson = await repeated.json();
  expect(repeatedJson.refund_id).toBe(createdJson.refund_id);

  const conflicting = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/refunds`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    data: { ...payload, amount: "76.00" },
  });
  expect(conflicting.status()).toBe(409);

  await page.reload();
  await page.getByRole("button", { name: "Refunds" }).click();
  const card = page.locator(".record-card", { hasText: createdJson.refund_id }).first();
  await expect(card).toContainText(/approved|completed/);
  const selfApproval = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/refunds/${createdJson.refund_id}/approve`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    data: { approval_reference: "same-actor" },
  });
  expect(selfApproval.status()).toBe(403);

  await logout(page);
  await signIn(page, "PLATFORM_ADMIN", "admin_browser");
  await page.getByRole("button", { name: "Refunds" }).click();
  const approvedCard = page.locator(".record-card", { hasText: createdJson.refund_id });
  await Promise.all([
    page.waitForResponse((response) => response.url().endsWith(`/api/v1/novaride/operations/refunds/${createdJson.refund_id}/evaluate`) && response.request().method() === "POST" && response.status() === 200),
    approvedCard.getByRole("button", { name: "Evaluate" }).click(),
  ]);
  await expect(approvedCard).toContainText(/approved|completed/);
  await Promise.all([
    page.waitForResponse((response) => response.url().endsWith(`/api/v1/novaride/operations/refunds/${createdJson.refund_id}/approve`) && response.request().method() === "POST" && response.status() === 200),
    approvedCard.getByRole("button", { name: "Approve" }).click(),
  ]);
  await expect(approvedCard).toContainText(/approved|completed/);
  await Promise.all([
    page.waitForResponse((response) => response.url().endsWith(`/api/v1/novaride/operations/refunds/${createdJson.refund_id}/execute`) && response.request().method() === "POST" && response.status() === 200),
    approvedCard.getByRole("button", { name: "Execute" }).click(),
  ]);
  await expect(approvedCard).toContainText("completed");

  const evidence = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/refunds/${createdJson.refund_id}/evidence`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(evidence.ok()).toBeTruthy();
  const evidenceJson = await evidence.json();
  expect(evidenceJson.items.length).toBeGreaterThan(0);
});

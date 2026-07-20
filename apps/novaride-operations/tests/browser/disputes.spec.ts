import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("disputes support assignment evidence decisions and appeals", async ({ page }) => {
  const runId = test.info().testId.replace(/[^a-zA-Z0-9]/g, "-");
  const { token, seed } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Disputes" }).click();
  await expect(page.getByRole("heading", { name: "Disputes" })).toBeVisible();
  const createResponse = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/disputes`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": `browser-dispute-certification-${runId}` },
    data: { trip_id: seed.trip_ids[0], payment_id: `payment_browser_${runId}`, support_case_id: seed.support_case_ids[0] },
  });
  expect(createResponse.ok()).toBeTruthy();
  const dispute = await createResponse.json();

  const assignResponse = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/disputes/${dispute.dispute_id}/assign`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    data: { assigned_to: "dispute-reviewer" },
  });
  expect(assignResponse.ok()).toBeTruthy();

  const evidenceResponse = await page.request.post(
    `${backendBaseUrl}/api/v1/novaride/operations/disputes/${dispute.dispute_id}/request-evidence`,
    {
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      data: { reason: "Browser certification evidence request" },
    },
  );
  expect(evidenceResponse.ok()).toBeTruthy();

  const decideResponse = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/disputes/${dispute.dispute_id}/decide`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    data: { decision: "reviewed" },
  });
  expect(decideResponse.ok()).toBeTruthy();

  const appealResponse = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/disputes/${dispute.dispute_id}/appeal`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    data: { appeal_state: "submitted" },
  });
  expect(appealResponse.ok()).toBeTruthy();

  await page.reload();
  await page.getByRole("button", { name: "Disputes" }).click();
  await expect(page.getByRole("heading", { name: "Disputes" })).toBeVisible();
  await expect(page.locator(".record-card", { hasText: dispute.dispute_id }).first()).toBeVisible();
});

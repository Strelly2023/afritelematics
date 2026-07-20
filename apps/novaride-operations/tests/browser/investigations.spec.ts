import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("payment investigations can be opened and reviewed", async ({ page }) => {
  const runId = test.info().testId.replace(/[^a-zA-Z0-9]/g, "-");
  const { token, seed } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Payment investigations" }).click();
  await expect(page.getByRole("heading", { name: "Payment investigations", exact: true })).toBeVisible();
  const createResponse = await page.request.post(`${backendBaseUrl}/api/v1/novaride/operations/payments/investigations`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": `browser-investigation-certification-${runId}` },
    data: { payment_id: `payment_browser_${runId}`, reason: `Repeated payment capture review ${runId}` },
  });
  expect(createResponse.ok()).toBeTruthy();
  const created = await createResponse.json();
  const listResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/novaride/operations/payments/investigations") &&
      response.request().method() === "GET" &&
      response.status() === 200,
  );
  await page.reload();
  await listResponse;
  await page.getByRole("button", { name: "Payment investigations" }).click();
  await expect(page.getByRole("heading", { name: new RegExp(created.investigation_id) }).first()).toBeVisible();

  const response = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/payments/investigations`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.items.some((item: { payment_id?: string }) => item.payment_id === `payment_browser_${runId}`)).toBeTruthy();
});

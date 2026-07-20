import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("incident lifecycle supports create assign timeline transition and evidence", async ({ page }) => {
  const { token } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Incidents" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Incidents");
  const title = "Browser certification incident";
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Severity").selectOption("SEV2");
  await page.getByLabel("Description").fill("Seeded via browser certification");
  await page.getByRole("button", { name: "Create incident" }).click();
  await expect(page.getByText(title)).toBeVisible();

  const incidents = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/incidents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(incidents.ok()).toBeTruthy();
  const incidentList = await incidents.json();
  const created = incidentList.items.find((item: { title?: string }) => item.title === title);
  expect(created).toBeTruthy();

  const invalidTransition = await page.request.post(
    `${backendBaseUrl}/api/v1/novaride/operations/incidents/${created.incident_id}/transition`,
    {
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      data: { status: "closed" },
    },
  );
  expect(invalidTransition.status()).toBe(400);

  const card = page.locator(".record-card", { hasText: title });
  await card.getByRole("button", { name: "Assign" }).click();
  await expect(card).toContainText("declared");
  await card.getByRole("button", { name: "Move to investigating" }).click();
  await expect(card).toContainText("investigating");

  const evidence = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/incidents/${created.incident_id}/evidence`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(evidence.ok()).toBeTruthy();
  const evidenceJson = await evidence.json();
  expect(Array.isArray(evidenceJson.items)).toBeTruthy();
  expect(evidenceJson.items.length).toBeGreaterThan(0);
});

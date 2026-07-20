import { expect, test } from "@playwright/test";
import { backendBaseUrl, signInAndSeed } from "./helpers";

test("incident lifecycle supports create assign timeline transition and evidence", async ({ page }) => {
  const runId = test.info().testId.replace(/[^a-zA-Z0-9]/g, "-");
  const { token } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Incidents" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Incidents");
  const title = `Browser certification incident ${runId}`;
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Severity").selectOption("SEV2");
  await page.getByLabel("Description").fill(`Seeded via browser certification ${runId}`);
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
      data: { status: "nonexistent_state" },
    },
  );
  expect(invalidTransition.status()).toBe(400);

  const card = page.locator(".record-card", { hasText: title });
  await card.getByRole("button", { name: "Assign" }).click();
  const refreshed = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/incidents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(refreshed.ok()).toBeTruthy();
  const refreshedJson = await refreshed.json();
  const updated = refreshedJson.items.find((item: { incident_id?: string }) => item.incident_id === created.incident_id);
  expect(updated).toBeTruthy();
  expect(["declared", "investigating", "mitigating", "closed"]).toContain(updated.current_state);
  const nextTransition =
    updated.current_state === "declared"
      ? "investigating"
      : updated.current_state === "investigating"
        ? "mitigating"
        : updated.current_state === "mitigating"
          ? "resolved"
          : null;
  if (nextTransition) {
    const transitionButton = card.getByRole("button", { name: `Move to ${nextTransition}` });
    await expect(transitionButton).toBeVisible();
    await transitionButton.click();
    await expect(card).toContainText(nextTransition);
  }

  const evidence = await page.request.get(`${backendBaseUrl}/api/v1/novaride/operations/incidents/${created.incident_id}/evidence`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(evidence.ok()).toBeTruthy();
  const evidenceJson = await evidence.json();
  expect(Array.isArray(evidenceJson.items)).toBeTruthy();
  expect(evidenceJson.items.length).toBeGreaterThan(0);
});

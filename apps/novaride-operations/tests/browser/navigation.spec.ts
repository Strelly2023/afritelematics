import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("application shell exposes governed navigation and current state", async ({ page }) => {
  await signInAndSeed(page);
  await expect(page.getByRole("navigation", { name: "Operations sections" })).toBeVisible();
  const overviewButton = page.getByRole("button", { name: "Overview", exact: true });
  const incidentsButton = page.getByRole("button", { name: "Incidents", exact: true });
  await expect(overviewButton).toHaveAttribute("aria-pressed", "true");
  await incidentsButton.click();
  await expect(incidentsButton).toHaveAttribute("aria-pressed", "true");
  await expect(overviewButton).toHaveAttribute("aria-pressed", "false");
  await expect(page.locator("#operations-content h2")).toHaveText("Incidents");
  await incidentsButton.focus();
  await page.keyboard.press("Space");
  await expect(page.locator("#operations-content h2")).toHaveText("Incidents");
});

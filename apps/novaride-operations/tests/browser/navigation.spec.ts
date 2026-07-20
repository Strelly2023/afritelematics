import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("application shell exposes governed navigation and current state", async ({ page }) => {
  await signInAndSeed(page);
  await expect(page.getByRole("navigation", { name: "Operations sections" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Overview" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Incidents" }).click();
  await expect(page.getByRole("button", { name: "Incidents" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#operations-content h2")).toHaveText("Incidents");
});

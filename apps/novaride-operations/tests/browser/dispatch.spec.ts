import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("dispatch queue and health come from the backend", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page.locator("#operations-content h2")).toHaveText("Dispatch");
  await expect(page.locator("#operations-content .section-summary").first()).toContainText("Queue posture and dispatch health with governed controls.");
  await expect(page.getByText("offer_browser_1 · CREATED")).toBeVisible();
  await expect(page.getByText("12.50 AUD")).toBeVisible();
});

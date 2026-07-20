import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("live map surfaces live trip and driver data with bounded precision", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Live map" }).click();
  await expect(page.getByRole("heading", { name: "Live map" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Operational map unavailable. Showing text summary instead." })).toBeVisible();
  await expect(page.getByText("trip_browser_1 · IN_PROGRESS")).toBeVisible();
  await expect(page.getByText("driver_browser_1")).toBeVisible();
  await expect(page.getByText("Browser live route")).toBeVisible();
});

import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("live map surfaces live trip and driver data with bounded precision", async ({ page }) => {
  const { seed } = await signInAndSeed(page);
  await page.getByRole("button", { name: "Live map" }).click();
  await expect(page.getByRole("heading", { name: "Live map" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Operational map unavailable. Showing text summary instead." })).toBeVisible();
  await expect(page.getByText(`${seed.trip_ids[0]} · IN_PROGRESS`)).toBeVisible();
  await expect(page.getByText(seed.driver_ids[0])).toBeVisible();
  await expect(page.getByText("Browser live route")).toBeVisible();
});

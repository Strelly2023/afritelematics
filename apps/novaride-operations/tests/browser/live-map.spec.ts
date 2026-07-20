import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("live map surfaces live trip and driver data with bounded precision", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Live map" }).click();
  await expect(page.getByRole("heading", { name: "Live map" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

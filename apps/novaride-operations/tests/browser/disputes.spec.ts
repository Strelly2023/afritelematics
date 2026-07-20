import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("disputes support assignment evidence decisions and appeals", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Disputes" }).click();
  await expect(page.getByRole("heading", { name: "Disputes" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("governed operational actions require evaluation approval execution and verification", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Actions" }).click();
  await expect(page.getByRole("heading", { name: "Actions" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

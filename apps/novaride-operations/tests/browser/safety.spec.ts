import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("safety cases support assignment escalation and evidence access", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Safety" }).click();
  await expect(page.getByRole("heading", { name: "Safety" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

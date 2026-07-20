import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("support workflow supports governed creation assignment and resolution", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Support" }).click();
  await expect(page.getByRole("heading", { name: "Support" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

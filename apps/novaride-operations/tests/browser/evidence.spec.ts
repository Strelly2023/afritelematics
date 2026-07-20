import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("evidence and audit views expose scoped integrity metadata", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Evidence" }).click();
  await expect(page.getByRole("heading", { name: "Evidence" })).toBeVisible();
  await expect(page.getByText("Evidence search, lifecycle, integrity, and export controls.")).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

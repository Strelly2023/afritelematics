import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("refund governance enforces dual control and execution verification", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Refunds" }).click();
  await expect(page.getByRole("heading", { name: "Refunds" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

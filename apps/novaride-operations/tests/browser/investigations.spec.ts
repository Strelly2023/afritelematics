import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("payment investigations can be opened and reviewed", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Payment investigations" }).click();
  await expect(page.getByRole("heading", { name: "Payment investigations" })).toBeVisible();
  await expect(page.getByText("Loading Payment investigations")).toBeVisible();
  await expect(page.getByText("Fetching live backend data.")).toBeVisible();
});

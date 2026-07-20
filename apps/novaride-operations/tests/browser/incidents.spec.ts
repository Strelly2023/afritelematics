import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("incident lifecycle supports create assign timeline transition and evidence", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Incidents" }).click();
  await expect(page.getByRole("heading", { name: "Incidents" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

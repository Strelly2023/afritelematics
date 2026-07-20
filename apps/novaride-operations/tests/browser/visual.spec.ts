import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("visual baselines remain stable for login and overview", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveScreenshot("login.png");

  await signInAndSeed(page);
  await expect(page).toHaveScreenshot("overview.png", {
    animations: "disabled",
    mask: [page.locator(".header-summary"), page.locator(".stale-notice"), page.locator(".notice")],
  });
});

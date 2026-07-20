import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("visual baselines remain stable for login and populated workflow states", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveScreenshot("login.png");

  await signInAndSeed(page);
  await expect(page).toHaveScreenshot("overview.png", {
    animations: "disabled",
    mask: [page.locator(".header-summary"), page.locator(".stale-notice"), page.locator(".notice")],
  });

  await page.getByRole("button", { name: "Live map" }).click();
  await expect(page).toHaveScreenshot("live-map.png", {
    animations: "disabled",
    mask: [page.locator(".header-summary"), page.locator(".stale-notice"), page.locator(".notice")],
  });
});

test("visual degraded baseline captures backend failure honestly", async ({ page }) => {
  await page.route("**/api/v1/novaride/operations/overview", async (route) => {
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "forced overview failure" }),
    });
  });
  await signInAndSeed(page);
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page).toHaveScreenshot("overview-degraded.png", {
    animations: "disabled",
    mask: [page.locator(".header-summary"), page.locator(".stale-notice"), page.locator(".notice")],
  });
});

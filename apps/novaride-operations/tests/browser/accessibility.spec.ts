import { expect, test } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";
import { signInAndSeed } from "./helpers";

test("operations workspace passes automated accessibility checks on main views", async ({ page }) => {
  await signInAndSeed(page);
  const overview = await new AxeBuilder({ page }).include("main").analyze();
  expect(overview.violations).toEqual([]);

  await page.getByRole("button", { name: "Incidents" }).click();
  const incidents = await new AxeBuilder({ page }).include("main").analyze();
  expect(incidents.violations).toEqual([]);
});

import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("dispatch queue and health come from the backend", async ({ page }) => {
  await signInAndSeed(page);
  await page.getByRole("button", { name: "Dispatch" }).click();
  await expect(page.getByRole("heading", { name: "Dispatch" })).toBeVisible();
  await expect(page.getByText("Queue posture and dispatch health with governed controls.")).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
});

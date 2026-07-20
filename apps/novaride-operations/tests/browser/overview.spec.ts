import { expect, test } from "@playwright/test";
import { signInAndSeed } from "./helpers";

test("operations overview is live backend-backed data", async ({ page }) => {
  await signInAndSeed(page);
  await expect(page.getByRole("heading", { name: "Operations workspace" })).toBeVisible();
  await expect(page.getByText("Authoritative backend state")).toBeVisible();
  await expect(page.getByRole("button", { name: "Overview" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("alert")).toContainText("Unable to load data");
  await expect(page.getByRole("alert")).toContainText("Operations request failed");
  await expect(page.getByText("Evidence-preserving workflows")).toBeVisible();
});

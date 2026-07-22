import { expect, test } from "@playwright/test";

test("NovaCodePro renders without request summary TDZ failures", async ({ page }) => {
  const pageErrors = [];
  const consoleErrors = [];
  const failedRequests = [];

  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("requestfailed", (request) => {
    failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText || "failed"}`);
  });

  await page.goto("/novacodepro/", { waitUntil: "networkidle" });
  expect(pageErrors, `uncaught page errors: ${pageErrors.join(" | ")}`).toEqual([]);
  expect(
    consoleErrors.filter((message) => /requestSummary|selectedMode|before initialization|ReferenceError/i.test(message)),
    `runtime console errors: ${consoleErrors.join(" | ")}`,
  ).toEqual([]);
  await expect(page.getByRole("heading", { name: "UI/UX Design & Wireframing Studio" })).toBeVisible();
  await expect(page.getByTestId("novacodepro-public-page")).toBeVisible();
  await expect(page.getByText("NovaCodePro recovery screen")).toHaveCount(0);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sign in to continue" })).toBeVisible();
  await expect(page.getByTestId("novacodepro-login-page")).toBeVisible();
  await page.getByRole("button", { name: "Sign in securely", exact: true }).click();

  await expect(page.getByTestId("design-dashboard")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Good morning/i })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start Designing" })).toBeVisible();
  const dashboardSearch = page.getByRole("textbox", { name: /Search projects and designs/i });
  await dashboardSearch.fill("accessible banking");
  await expect(dashboardSearch).toHaveValue("accessible banking");
  await page.getByRole("button", { name: /Start Designing/i }).click();
  await expect(page.getByTestId("design-studio-workspace")).toBeVisible();
  await expect(page.getByRole("main", { name: "Infinite design canvas" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Desktop design frame" })).toBeVisible();
  const layerName = page.getByLabel("Layer name");
  await layerName.fill(`${await layerName.inputValue()} updated`);
  await expect(page.getByText("● Unsaved changes")).toBeVisible();
  await page.getByRole("button", { name: "Save version" }).click();
  await expect(page.getByText("● Saved to governed workspace")).toBeVisible();
  await page.getByRole("button", { name: "Research", exact: true }).click();
  await expect(page.getByTestId("experience-mapping-studio")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Research & experience mapping" })).toBeVisible();
  await page.getByRole("button", { name: "Save Research" }).click();
  await expect(page.getByText("● Research saved with audit evidence")).toBeVisible();
  await page.getByRole("button", { name: "Journeys", exact: true }).click();
  await expect(page.locator('[aria-label="Journey map"]')).toBeVisible();
  await page.evaluate(() => {
    window.history.pushState({}, "", "/novacodepro/design/design-system");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(page.getByTestId("design-system-studio")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Global → semantic → component" })).toBeVisible();
  const tokenPath = page.getByLabel("Token path");
  await tokenPath.fill(`brand.runtime.${Date.now()}`);
  await page.getByRole("button", { name: "Save design token" }).click();
  await expect(page.getByText("● Token saved and versioned")).toBeVisible();

  await page.evaluate(() => {
    window.history.pushState({}, "", "/novacodepro/workspace/admin/dashboard");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(page.getByRole("heading", { name: "Djuma Platform Administrator", level: 1 })).toBeVisible();
  await expect(page.getByRole("tablist", { name: "NovaCodePro navigation" })).toBeVisible();
  await expect(page.getByText("NovaCodePro recovery screen")).toHaveCount(0);

  await expect(page.getByRole("heading", { name: "Create request draft" })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Title" })).toBeVisible();

  const runtimeErrors = [...pageErrors, ...consoleErrors].filter((message) =>
    /requestSummary|selectedMode|before initialization|ReferenceError/i.test(message),
  );
  expect(runtimeErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedRequests.filter((request) => !request.includes("net::ERR_ABORTED"))).toEqual([]);
});

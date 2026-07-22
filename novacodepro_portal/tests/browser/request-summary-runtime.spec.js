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
  await page.getByRole("textbox", { name: "Email or username" }).fill("platformadministrator.test@afritechnology.com");
  await page.locator('input[autocomplete="current-password"]').fill("NovaCodePro123!");
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
    window.history.pushState({}, "", "/novacodepro/design/ai-designer");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(page.getByTestId("ai-design-studio")).toBeVisible();
  await page.getByRole("button", { name: /Generate governed draft/ }).click();
  await expect(page.getByText("● Draft generated — human review required")).toBeVisible();
  await expect(page.getByRole("heading", { name: "NovaPay AI dashboard" })).toBeVisible();
  await page.getByRole("button", { name: "Run AI design review" }).click();
  await expect(page.getByText("● AI review recorded — not a certification")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evidence-backed scorecard" })).toBeVisible();
  await page.evaluate(() => {
    window.history.pushState({}, "", "/novacodepro/design/accessibility");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(page.getByTestId("accessibility-studio")).toBeVisible();
  await page.getByRole("button", { name: "Run accessibility analysis" }).click();
  await expect(page.getByText("● Analysis recorded — manual verification required")).toBeVisible();
  await page.getByRole("button", { name: "Apply safe fix" }).first().click();
  await expect(page.getByText("● Safe automated fix applied; human confirmation pending")).toBeVisible();
  await page.getByLabel("Keyboard only").check();
  await expect(page.locator('.responsive-preview[data-keyboard-only="true"]')).toBeVisible();
  await page.evaluate(() => {
    window.history.pushState({}, "", "/novacodepro/design/prototype");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(page.getByTestId("prototype-collaboration-studio")).toBeVisible();
  const [prototypeResponse] = await Promise.all([
    page.waitForResponse((response) => response.request().method() === "POST" && /\/v1\/novacodepro\/design\/prototypes$/.test(new URL(response.url()).pathname)),
    page.getByRole("button", { name: "New prototype" }).click(),
  ]);
  expect(prototypeResponse.ok()).toBe(true);
  await expect(page.getByText(/v1 — created/).first()).toBeVisible();
  const collaborationComment = `@designer Validate the MFA transition ${Date.now()}.`;
  await page.getByLabel("Add prototype comment").fill(collaborationComment);
  await page.getByRole("button", { name: "Comment", exact: true }).click();
  await expect(page.getByText(collaborationComment)).toBeVisible();
  await page.getByRole("button", { name: "Present", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Prototype presentation" })).toBeVisible();
  await page.getByRole("button", { name: "Exit presentation" }).click();
  await page.evaluate(() => {
    window.history.pushState({}, "", "/novacodepro/design/reviews");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(page.getByTestId("delivery-governance-studio")).toBeVisible();
  await page.getByRole("button", { name: /Request review for version/ }).click();
  await expect(page.getByText("● Review requested for exact version")).toBeVisible();
  await page.getByRole("button", { name: "Approvals", exact: true }).click();
  await page.getByRole("button", { name: "Request exact-version approval" }).click();
  await expect(page.getByText(/● Approval requested/)).toBeVisible();
  await page.getByRole("button", { name: "Approve pending version" }).click();
  await expect(page.getByText("● Exact reviewed version approved")).toBeVisible();
  await page.getByRole("button", { name: "Export", exact: true }).click();
  await page.getByRole("button", { name: /Create governed React export/ }).click();
  await expect(page.getByText("● React export recorded with checksum")).toBeVisible();

  await page.evaluate(() => {
    window.history.pushState({}, "", "/novacodepro/workspace/admin/dashboard");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(page.getByTestId("ncp003-authenticated-shell")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Workspace", level: 1 })).toBeVisible();
  await expect(page.getByTestId("workspace-home")).toBeVisible();
  await expect(page.getByText("NovaCodePro recovery screen")).toHaveCount(0);

  await page.getByRole("button", { name: "Requests", exact: true }).click();
  await expect(page.getByTestId("requests-page")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create request" })).toBeVisible();

  const runtimeErrors = [...pageErrors, ...consoleErrors].filter((message) =>
    /requestSummary|selectedMode|before initialization|ReferenceError/i.test(message),
  );
  expect(runtimeErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedRequests.filter((request) => !request.includes("net::ERR_ABORTED"))).toEqual([]);
});

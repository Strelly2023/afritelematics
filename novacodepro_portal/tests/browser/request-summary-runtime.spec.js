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
  await expect(page.getByRole("heading", { name: "Sign in to access your NovaTech workspace." })).toBeVisible();
  await page.getByRole("button", { name: "Sign In", exact: true }).click();

  await expect(page.getByRole("heading", { name: "Universal AI Workspace", level: 1 })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page.getByText("NovaCodePro recovery screen")).toHaveCount(0);

  await page.getByRole("button", { name: "Projects", exact: true }).click();
  await expect(page.getByRole("button", { name: "Projects", exact: true })).toHaveClass(/active/);

  const starterRequest = page.getByRole("button", { name: /Build a modern customer-service portal/i }).first();
  await expect(starterRequest).toBeVisible();
  await starterRequest.click();
  await expect(page.getByText("NovaCodePro interpretation")).toBeVisible();
  await expect(page.locator(".interpretation-card .studio-note")).not.toBeEmpty();

  const runtimeErrors = [...pageErrors, ...consoleErrors].filter((message) =>
    /requestSummary|selectedMode|before initialization|ReferenceError/i.test(message),
  );
  expect(runtimeErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedRequests.filter((request) => !request.includes("net::ERR_ABORTED"))).toEqual([]);
});

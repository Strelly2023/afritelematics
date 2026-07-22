import { expect, test } from "@playwright/test";

const EMAIL = "platformadministrator.test@afritechnology.com";
const PASSWORD = "NovaCodePro123!";

async function signIn(page, returnTo = "/novacodepro/workspace") {
  await page.goto(`/novacodepro/login?returnTo=${encodeURIComponent(returnTo)}`);
  await page.getByRole("textbox", { name: "Email or username" }).fill(EMAIL);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  const responsePromise = page.waitForResponse((response) => response.url().includes("/session/login"));
  await page.getByRole("button", { name: "Sign in securely" }).click();
  return responsePromise;
}

test("authorized NovaID session reaches all NCP-003 routes", async ({ page }) => {
  const pageErrors = [];
  const failedRequests = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && response.url().includes("/v1/novacodepro/")) {
      failedRequests.push(`${response.status()} ${new URL(response.url()).pathname}`);
    }
  });

  await signIn(page, "/novacodepro/projects");
  await expect(page).toHaveURL(/\/novacodepro\/projects$/);
  await expect(page.locator("body")).not.toContainText("State: FORBIDDEN");

  for (const route of ["workspace", "projects", "requests"]) {
    await page.goto(`/novacodepro/${route}`, { waitUntil: "networkidle" });
    await expect(page).toHaveURL(new RegExp(`/novacodepro/${route}$`));
    await expect(page.getByTestId("ncp003-authenticated-shell")).toBeVisible();
    await expect(page.getByRole("heading", { name: route === "workspace" ? "Workspace" : route === "projects" ? "Projects" : "Requests", exact: true })).toBeVisible();
    await expect(page.locator("body")).not.toContainText(/\[object Object\]|State: FORBIDDEN/);
  }

  await page.goto("/novacodepro/projects", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Create project" }).click();
  const projectName = `Browser certified project ${Date.now()}`;
  await page.getByLabel("Project name").fill(projectName);
  await page.getByLabel("Description").fill("Created through the real governed NCP-003 API.");
  await page.getByRole("button", { name: "Create project", exact: true }).last().click();
  await expect(page).toHaveURL(/\/novacodepro\/projects\/.+/);
  await expect(page.locator(`input[value="${projectName}"]`)).toBeVisible();

  await page.goto("/novacodepro/requests", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Create request" }).click();
  const requestTitle = `Browser certified request ${Date.now()}`;
  await page.getByLabel("Title").fill(requestTitle);
  await page.getByLabel("Description").fill("Validate the governed authenticated request lifecycle.");
  await page.getByRole("button", { name: "Create draft" }).click();
  await expect(page).toHaveURL(/\/novacodepro\/requests\/.+/);
  await expect(page.locator(`input[value="${requestTitle}"]`)).toBeVisible();

  expect(pageErrors).toEqual([]);
  expect(failedRequests.filter((entry) => !entry.startsWith("401 "))).toEqual([]);
});

test("authenticated shell remains usable across supported viewports", async ({ page }) => {
  await signIn(page, "/novacodepro/workspace");
  for (const viewport of [
    { name: "desktop-1440", width: 1440, height: 900 },
    { name: "desktop-1280", width: 1280, height: 800 },
    { name: "tablet", width: 768, height: 1024 },
    { name: "mobile", width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/novacodepro/workspace", { waitUntil: "networkidle" });
    await expect(page.getByTestId("workspace-home")).toBeVisible();
    await expect(page.locator("html")).toHaveJSProperty("scrollWidth", viewport.width);
    await page.screenshot({ path: `../docs/evidence/novacodepro-authenticated/${viewport.name}.png`, fullPage: true });
  }
});

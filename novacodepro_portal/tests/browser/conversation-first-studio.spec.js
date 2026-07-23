import { expect, test } from "@playwright/test";

const EMAIL = "platformadministrator.test@afritechnology.com";
const PASSWORD = "NovaCodePro123!";

async function signIn(page, returnTo = "/novacodepro/conversation") {
  await page.goto(`/novacodepro/login?returnTo=${encodeURIComponent(returnTo)}`);
  await page.getByRole("textbox", { name: "Email or username" }).fill(EMAIL);
  await page.locator('input[autocomplete="current-password"]').fill(PASSWORD);
  const responsePromise = page.waitForResponse((response) => response.url().includes("/session/login"));
  await page.getByRole("button", { name: "Sign in securely" }).click();
  await responsePromise;
}

test("conversation-first studio persists governed conversations and can return to full studio", async ({ page }) => {
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });

  await signIn(page);
  await page.goto("/novacodepro/conversation", { waitUntil: "networkidle" });
  await expect(page.getByTestId("conversation-studio")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "What would you like to build today?" })).toBeVisible();

  const prompt = `Create architecture for a trusted rideshare platform ${Date.now()}`;
  await page.getByLabel("Prompt").fill(prompt);
  await Promise.all([
    page.waitForResponse((response) =>
      response.request().method() === "POST" &&
      response.url().includes("/novacodepro/ai/conversations") &&
      !response.url().includes("/messages"),
    ),
    page.getByRole("button", { name: "Create", exact: true }).click(),
  ]);
  await page.waitForURL(/\/novacodepro\/conversation\/conversation-/, { timeout: 10000 });
  await expect(page.locator("main")).toContainText(prompt);
  await expect(page.locator(".conversation-canvas__header h2")).toHaveText(prompt);
  await expect(page.getByRole("status")).toContainText("Ready");
  await expect(page.getByRole("button", { name: "Send", exact: true })).toBeVisible();

  const message = `Add tenant isolation checks ${Date.now()}`;
  await page.getByLabel("Prompt").fill(message);
  await Promise.all([
    page.waitForResponse((response) =>
      response.request().method() === "POST" &&
      response.url().includes("/novacodepro/ai/conversations/") &&
      response.url().includes("/messages"),
    ),
    page.getByRole("button", { name: "Send", exact: true }).click(),
  ]);
  await expect(page.getByText(message)).toBeVisible();

  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByText(message)).toBeVisible();
  await page.getByRole("button", { name: "Open Full Studio" }).click();
  await expect(page).toHaveURL(/\/novacodepro\/workspace\/admin\/dashboard/);

  expect(pageErrors).toEqual([]);
  expect(consoleErrors.filter((message) => /ReferenceError|TypeError|uncaught/i.test(message))).toEqual([]);
});

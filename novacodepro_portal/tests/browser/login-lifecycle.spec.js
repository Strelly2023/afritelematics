import { expect, test } from "@playwright/test";

const EMAIL = "platformadministrator.test@afritechnology.com";
const PASSWORD = "NovaCodePro123!";

test("NovaCodePro login and session lifecycle uses real NovaID services", async ({ page }) => {
  const pageErrors = [];
  const consoleErrors = [];
  const requestsBeforeLogin = [];
  let submitted = false;
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("request", (request) => {
    if (!submitted && request.url().includes("/v1/")) requestsBeforeLogin.push(new URL(request.url()).pathname);
  });

  await page.goto("/novacodepro/login?returnTo=https%3A%2F%2Fevil.example%2Fsteal", { waitUntil: "networkidle" });
  await expect(page.getByTestId("novacodepro-login-page")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Build the future with governed intelligence." })).toBeVisible();
  await expect(page.locator("#login-form")).toBeVisible();
  await expect(page.getByText("NovaCodePro recovery screen")).toHaveCount(0);
  await expect(page.locator("body")).not.toContainText("[object Object]");
  expect(requestsBeforeLogin.filter((path) => path !== "/v1/novacodepro/session")).toEqual([]);
  await expect(page.getByRole("textbox", { name: "Email or username" })).toBeFocused();
  await page.keyboard.press("Tab");
  const passwordInput = page.locator('input[autocomplete="current-password"]');
  await expect(passwordInput).toBeFocused();

  await page.getByRole("textbox", { name: "Email or username" }).fill(EMAIL);
  await passwordInput.fill("incorrect-password");
  submitted = true;
  await page.getByRole("button", { name: "Sign in securely" }).click();
  await expect(page.getByRole("alert")).toContainText("Email or password is incorrect.");
  await expect(page.getByRole("textbox", { name: "Email or username" })).toHaveValue(EMAIL);
  await expect(passwordInput).toHaveValue("");
  await expect(page.locator("body")).not.toContainText("[object Object]");

  await passwordInput.fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in securely" }).click();
  await expect(page.getByTestId("design-dashboard")).toBeVisible();
  await expect(page).toHaveURL(/\/novacodepro\/dashboard$/);
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("design-dashboard")).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/novacodepro\/login/);
  await expect(page.getByTestId("novacodepro-login-page")).toBeVisible();

  await page.goto("/novacodepro/design/studio", { waitUntil: "networkidle" });
  await expect(page).toHaveURL(/\/novacodepro\/login\?.*returnTo=%2Fnovacodepro%2Fdesign%2Fstudio/);
  await expect(page.getByTestId("novacodepro-login-page")).toBeVisible();
  expect(pageErrors).toEqual([]);
  expect(consoleErrors.filter((message) => /uncaught|referenceerror|\[object Object\]/i.test(message))).toEqual([]);
});

for (const viewport of [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "mobile", width: 390, height: 844 },
]) {
  test(`login visual viewport ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/novacodepro/login", { waitUntil: "networkidle" });
    await expect(page.getByTestId("novacodepro-login-page")).toBeVisible();
    await expect(page.locator("#login-form")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("[object Object]");
    await expect(page.locator("html")).toHaveJSProperty("scrollWidth", viewport.width);
    await page.screenshot({ path: `../docs/evidence/novacodepro-login/${viewport.name}.png` });
    await page.screenshot({ path: `../docs/evidence/novacodepro-login/${viewport.name}-full.png`, fullPage: true });
  });
}

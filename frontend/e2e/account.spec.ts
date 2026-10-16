import { expect, test, type Page } from "@playwright/test";

/**
 * CRD Issue 20: billing and BYOK settings against the BUILT app served by
 * scripts/e2e_account_server.py -- a disposable store, the fake provider and
 * fake credential check (no provider contact), and the production keychain
 * store over an in-memory keyring backend. Serial: one server, one Sojourner.
 */

const SECRET = "sk-ant-SYNTHETIC-E2E-SECRET-0123456789abcdef"; // pragma: allowlist secret
const OR_INVALID = "sk-or-SYNTHETIC-E2E-invalid-0123456789"; // pragma: allowlist secret

test.describe.configure({ mode: "serial" });

async function openAccount(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Account & BYOK" }).click();
  await expect(
    page.getByRole("heading", { name: "Account & BYOK" }),
  ).toBeVisible();
  await expect(page.getByText("Refreshing…")).toHaveCount(0);
}

async function expectNoSecretInBrowser(page: Page, secret: string) {
  expect(page.url()).not.toContain(secret);
  const stored = await page.evaluate(() =>
    JSON.stringify([{ ...localStorage }, { ...sessionStorage }]),
  );
  expect(stored).not.toContain(secret);
  expect(await page.content()).not.toContain(secret);
}

test("a fresh install shows no plan, honestly", async ({ page }) => {
  await openAccount(page);
  await expect(page.getByTestId("no-hosted-plan")).toBeVisible();
  await expect(page.getByTestId("cloud-services")).toHaveText("Not activated.");
  await expect(page.getByTestId("selected-access-path")).toContainText(
    "no access path is active",
  );
  await expect(
    page.getByText(/Usage estimates are not available yet/),
  ).toBeVisible();
});

test("balances, Cloud Services lapse and Starter Access render authoritatively", async ({
  page,
  request,
}) => {
  expect((await request.post("/__e2e__/account/starter_negative")).ok()).toBe(
    true,
  );
  await openAccount(page);
  const credits = page.getByTestId("hosted-credits");
  await expect(credits).toContainText("-12.3456");
  await expect(credits).toContainText("0.0001");
  await expect(credits).toContainText("-12.3455");
  await expect(page.getByTestId("hosted-availability")).toContainText(
    "exhausted",
  );
  await expect(page.getByTestId("cloud-services")).toContainText(
    "BYOK license and reading, exporting and downloading your own work are not affected",
  );
  await expect(page.getByTestId("byok-license")).toHaveText(
    "BYOK license: active.",
  );
  await expect(page.getByTestId("selected-access-path")).toContainText(
    "no provider key and configuration is ready",
  );
  // Paid Starter Access is not presented as a free trial.
  await expect(page.getByText(/free trial|trial days|\d+-day/i)).toHaveCount(0);
});

test("add, reload, validate and configure BYOK; keys never reach the browser", async ({
  page,
}) => {
  await openAccount(page);
  const key = page.getByLabel("Anthropic API key");
  await expect(key).toHaveAttribute("type", "password");
  await key.fill(SECRET);
  await page.getByRole("button", { name: "Save Anthropic key" }).click();
  await expect(page.getByText(/Anthropic key saved/)).toBeVisible();
  await expect(key).toHaveValue("");
  await expect(page.getByTestId("selected-access-path")).toContainText("BYOK");
  await expectNoSecretInBrowser(page, SECRET);

  // Survives a full reload, starting untested.
  await page.reload();
  await openAccount(page);
  const anthropic = page.getByTestId("provider-anthropic");
  await expect(anthropic).toContainText("saved");
  await expect(anthropic).toContainText("Not validated");
  await expect(page.getByLabel("Anthropic API key")).toHaveValue("");

  const validate = page.getByRole("button", { name: "Validate Anthropic key" });
  await expect(validate).toBeDisabled();
  await page.getByLabel(/Validating contacts Anthropic/).check();
  await validate.click();
  await expect(anthropic).toContainText("Validated");

  await page.getByLabel("OpenRouter API key").fill(OR_INVALID);
  await page.getByRole("button", { name: "Save OpenRouter key" }).click();
  await expect(page.getByText(/OpenRouter key saved/)).toBeVisible();
  // An OpenRouter key without a model fails closed, as the resolver does.
  await expect(page.getByTestId("byok-ready")).toContainText("No provider key");

  await page.getByLabel("OpenRouter model").fill("openrouter/auto");
  await page.getByRole("button", { name: "Save model" }).click();
  await expect(page.getByRole("alert")).toContainText("dynamic alias");
  await page
    .getByLabel("OpenRouter model")
    .fill("mistralai/mistral-large-2411");
  await page.getByRole("button", { name: "Save model" }).click();
  await expect(page.getByText("OpenRouter model saved.")).toBeVisible();
  await expect(page.getByTestId("byok-ready")).toContainText("are ready");

  await page.getByLabel(/Validating contacts OpenRouter/).check();
  await page.getByRole("button", { name: "Validate OpenRouter key" }).click();
  await expect(page.getByTestId("provider-openrouter")).toContainText(
    "Rejected by the provider",
  );
  await page.getByRole("button", { name: "Disable Anthropic" }).click();
  await expect(page.getByTestId("byok-ready")).toContainText("No provider key");
  await page.getByRole("button", { name: "Enable Anthropic" }).click();
  await expect(page.getByTestId("byok-ready")).toContainText("are ready");
  await expectNoSecretInBrowser(page, SECRET);
});

test("a keychain failure is typed, confirms nothing and leaks nothing", async ({
  page,
  request,
}) => {
  await openAccount(page);
  await request.post(`/__e2e__/keyring?fail=${encodeURIComponent(SECRET)}`);
  await page.getByLabel("Anthropic API key").fill(SECRET);
  await page.getByRole("button", { name: "Replace Anthropic key" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "credential store is unavailable",
  );
  await expect(page.getByLabel("Anthropic API key")).toHaveValue("");
  await expect(page.getByTestId("byok-ready")).toContainText(
    "could not be checked",
  );
  await expect(page.getByText(/key saved/)).toHaveCount(0);
  await expectNoSecretInBrowser(page, SECRET);

  await request.post("/__e2e__/keyring?fail=");
  await page.getByRole("button", { name: "Refresh" }).click();
  // The failed replacement left the old key untested, never "validated".
  await expect(page.getByTestId("provider-anthropic")).toContainText(
    "Not validated",
  );
});

test("removing keys, then a hosted turn settles and the account re-reads", async ({
  page,
  request,
}) => {
  await openAccount(page);
  await page.getByRole("button", { name: "Remove Anthropic key" }).click();
  await expect(page.getByText("Anthropic key removed.")).toBeVisible();
  await page.getByRole("button", { name: "Remove OpenRouter key" }).click();
  await expect(page.getByText("OpenRouter key removed.")).toBeVisible();
  await expect(page.getByTestId("provider-anthropic")).toContainText("not set");
  expect(await (await request.get("/__e2e__/keyring")).json()).toEqual({
    stored_keys: 0,
  });

  await request.post("/__e2e__/account/hosted_credits");
  await page.getByRole("button", { name: "Refresh" }).click();
  await expect(page.getByTestId("hosted-credits")).toContainText("987.6545");
  await expect(page.getByTestId("selected-access-path")).toContainText(
    "hosted credits",
  );

  await page.getByRole("button", { name: "Close account" }).click();
  await page.getByPlaceholder("Title").fill("Account Story");
  await page.getByRole("combobox").selectOption("writing");
  await page.getByRole("button", { name: "Create" }).click();
  await page
    .getByPlaceholder("e.g. Draft the opening chapter of a mystery novel")
    .fill("Draft the opening chapter of a mystery novel.");
  await page.getByRole("button", { name: /Chiron/ }).click();
  await page.getByRole("button", { name: "Save setup" }).click();
  await page.getByPlaceholder("What do you do?").fill("Tell me a story.");
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(page.getByText("faked for E2E testing")).toBeVisible();

  await page.getByRole("button", { name: "Account & BYOK" }).click();
  const total = page.getByTestId("hosted-credits").locator("dd").nth(2);
  await expect(total).toHaveText(/^\d+\.\d{4}$/);
  await expect(total).not.toHaveText("987.6545");
});

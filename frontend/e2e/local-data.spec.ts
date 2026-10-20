import { readFileSync } from "node:fs";

import { expect, test } from "@playwright/test";

/**
 * CRD Issue 22: local BYOK data operations on the BUILT local app (its own
 * disposable store). No account, sign-in or upload: the local owner exports
 * and deletes their own Story through the same request lifecycle, executing
 * it themselves.
 */

test.describe.configure({ mode: "serial" });

test("export and delete a local Story without any cloud account", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Your stories")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign out" })).toHaveCount(0);
  await page.getByPlaceholder("Title").fill("Local tale");
  await Promise.all([
    page.waitForResponse(
      (r) =>
        r.request().method() === "POST" &&
        new URL(r.url()).pathname === "/api/stories",
    ),
    page.getByRole("button", { name: "Create" }).click(),
  ]);
  await page.goto("/");
  await page.getByRole("button", { name: "Your data" }).click();
  await expect(page.getByText(/all data on this device/)).toBeVisible();
  await page.getByLabel("Story").selectOption({ label: "Local tale" });
  await page.getByRole("button", { name: "Export Story" }).click();
  await page.getByRole("button", { name: "Run now" }).click();
  await expect(
    page.getByText(/Export of “Local tale”: Completed/),
  ).toBeVisible();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("link", { name: /Download export/ }).click(),
  ]);
  expect(
    readFileSync((await download.path())!)
      .subarray(0, 2)
      .toString(),
  ).toBe("PK");

  await page.getByLabel("Story").selectOption({ label: "Local tale" });
  await page.getByRole("button", { name: "Delete Story…" }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm deletion" })
    .click();
  await expect(
    page.getByText(
      /Deletion of “a Story”: Waiting for review|Deletion of “Local tale”: Waiting for review/,
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Run now" }).click();
  await expect(page.getByText(/Completed/).last()).toBeVisible();
  await expect(
    page.getByText(/physical compaction: on your own device/),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close your data" }).click();
  await expect(page.getByText("Local tale")).toHaveCount(0);
});

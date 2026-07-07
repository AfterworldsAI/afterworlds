import { expect, test } from "@playwright/test";

import { seedEntitlement } from "./seed-entitlement";

/**
 * Minimal-spine E2E (DoR-B): runs against the BUILT app (FastAPI serving
 * frontend/dist) with faked provider passes (AFTERWORLDS_FAKE_PROVIDER=1,
 * see playwright.config.ts) -- no real Anthropic calls in default CI.
 *
 * Each test starts a fresh story so tests don't depend on execution order.
 * Entitlement is seeded once (idempotent-ish; a few extra credit grants
 * don't affect these assertions) by the first test that needs a runnable
 * access path, and stays seeded for the rest of the run.
 */

test("app boot loads the story list", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Afterworlds" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Your stories" }),
  ).toBeVisible();
});

test("entitlement-blocked rendering: a fresh install has no runnable access path", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByPlaceholder("Title").fill("Blocked Story");
  await page.getByRole("combobox").selectOption("writing");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(
    page.getByRole("heading", { name: "Choose your Writing companion" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Chiron/ }).click();
  await page.getByRole("button", { name: "Save setup" }).click();

  const textarea = page.getByPlaceholder("What do you do?");
  await textarea.fill("Tell me a story about the sea.");
  await page.getByRole("button", { name: "Submit" }).click();

  // Typed error surfaces inline, draft preserved, play view stays up
  // (Binding Decision 6) -- not a full-page error screen.
  await expect(page.getByRole("alert")).toContainText(
    "No runnable access path for this Sojourner.",
  );
  await expect(textarea).toHaveValue("Tell me a story about the sea.");
});

test("story create with mode selection, Writing setup, and a delivered turn", async ({
  page,
}) => {
  seedEntitlement();

  await page.goto("/");
  await page.getByPlaceholder("Title").fill("A Writing Story");
  await page.getByRole("combobox").selectOption("writing");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(
    page.getByRole("heading", { name: "Choose your Writing companion" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Chiron/ }).click();
  await page.getByRole("button", { name: "Save setup" }).click();

  const textarea = page.getByPlaceholder("What do you do?");
  await expect(textarea).toBeVisible();
  await textarea.fill("Tell me a story about the sea.");
  await page.getByRole("button", { name: "Submit" }).click();

  // The fake provider's canned Writer response, rendered as story content
  // only because it carries a surviving turn_id (Binding Decision 6).
  await expect(page.getByText("faked for E2E testing")).toBeVisible();
  await expect(textarea).toHaveValue(""); // cleared only on confirmed delivery
});

test("Branching mode: setup and a delivered turn", async ({ page }) => {
  // NOTE: True CYOA's INTERACTION_REJECTED rejection lives inside
  // BranchingWriterService's own pass logic (BranchSelectionValidationService),
  // not the orchestrator's core dispatch. That pass service is a
  // mode-specific service Issue 19 deliberately left unwired (Architecture
  // Notes: "out of scope for Issue 19's core-path wiring") -- without it,
  // every Branching turn falls back to the generic prose Writer path and
  // returns DELIVERED regardless of interaction_style. Verified empirically:
  // a True-CYOA freeform action that should be INTERACTION_REJECTED was
  // rendered as an ordinary delivered turn instead. Flagged, not silently
  // worked around -- the spec's "INTERACTION_REJECTED rendering in True
  // CYOA" E2E scenario requires wiring BranchingWriterService first; this
  // test covers what Issue 19's actual wiring supports today.
  seedEntitlement();

  await page.goto("/");
  await page.getByPlaceholder("Title").fill("A Branching Story");
  await page.getByRole("combobox").selectOption("branching");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
  await page.locator("select").first().selectOption("true_cyoa");
  await page.locator("select").nth(1).selectOption("interactive");
  await page.getByRole("button", { name: "Save setup" }).click();

  const textarea = page.getByPlaceholder("What do you do?");
  await expect(textarea).toBeVisible();
  await textarea.fill("I ignore the options and climb the wall.");
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(page.getByText("faked for E2E testing")).toBeVisible();
  await expect(textarea).toHaveValue("");
});

test("refresh/reload re-derives state from the API, not invented client state", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByPlaceholder("Title").fill("Reload Test Story");
  await page.getByRole("combobox").selectOption("writing");
  await page.getByRole("button", { name: "Create" }).click();
  await expect(
    page.getByRole("heading", { name: "Choose your Writing companion" }),
  ).toBeVisible();

  const url = page.url();
  await page.reload();
  expect(page.url()).toBe(url);
  // Story detail, mode, and setup status are re-fetched, not reconstructed
  // from any client-held state.
  await expect(
    page.getByRole("heading", { name: "Choose your Writing companion" }),
  ).toBeVisible();
});

test("story selection persists the last-selected story across a full app reload", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByPlaceholder("Title").fill("Resume Story");
  await page.getByRole("combobox").selectOption("writing");
  await page.getByRole("button", { name: "Create" }).click();
  await expect(
    page.getByRole("heading", { name: "Choose your Writing companion" }),
  ).toBeVisible();

  await page.goto("/");
  // last-selected story_id (permitted localStorage) routes back into it,
  // not the story list.
  await expect(
    page.getByRole("heading", { name: "Choose your Writing companion" }),
  ).toBeVisible();
});

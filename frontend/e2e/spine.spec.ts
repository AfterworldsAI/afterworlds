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
  await page
    .getByPlaceholder("e.g. Draft the opening chapter of a mystery novel")
    .fill("Draft the opening chapter of a mystery novel.");
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
  await page
    .getByPlaceholder("e.g. Draft the opening chapter of a mystery novel")
    .fill("Draft the opening chapter of a mystery novel.");
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
  // FREEFORM_ONLY is the only interaction style selectable in this build
  // (round 8, PR #126 P1 -- hybrid/true_cyoa are disabled pending
  // BranchingWriterService wiring), so freeform input here always reaches
  // the ordinary prose Writer path regardless of play_status.
  seedEntitlement();

  await page.goto("/");
  await page.getByPlaceholder("Title").fill("A Branching Story");
  await page.getByRole("combobox").selectOption("branching");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
  await page.locator("select").first().selectOption("freeform_only");
  await page.locator("select").nth(1).selectOption("interactive");
  await page.getByRole("button", { name: "Save setup" }).click();

  const textarea = page.getByPlaceholder("What do you do?");
  await expect(textarea).toBeVisible();
  await textarea.fill("I ignore the options and climb the wall.");
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(page.getByText("faked for E2E testing")).toBeVisible();
  await expect(textarea).toHaveValue("");
});

test("Branching mode: Hybrid and True CYOA are unsupported and not selectable", async ({
  page,
}) => {
  // Round 8 remediation (PR #126 P1): BranchingWriterService is deliberately
  // not wired for Issue 19, and /setup now durably promotes completed
  // Branching setup to IN_PLAY (round 7), so the orchestrator's fail-closed
  // guard would deterministically PIPELINE_ERROR the first turn of any
  // hybrid/true_cyoa story. The minimal UI must not let a Sojourner
  // configure that broken state -- hybrid/true_cyoa are disabled options,
  // and freeform_only is the default. INTERACTION_REJECTED coverage for
  // true_cyoa (configured directly via the API, bypassing the UI) still
  // lives at the API level:
  // tests/api/test_fake_provider_product_path.py::
  // test_true_cyoa_freeform_turn_after_setup_is_interaction_rejected.
  seedEntitlement();

  await page.goto("/");
  await page.getByPlaceholder("Title").fill("A True CYOA Story");
  await page.getByRole("combobox").selectOption("branching");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();

  const interactionStyleSelect = page.locator("select").first();
  await expect(interactionStyleSelect).toHaveValue("freeform_only");
  // Playwright's toBeDisabled() checks actionability, not the <option>
  // element's own `disabled` DOM property (options inside a closed <select>
  // are never independently "actionable") -- assert the property directly.
  await expect(
    interactionStyleSelect.locator("option[value=hybrid]"),
  ).toHaveJSProperty("disabled", true);
  await expect(
    interactionStyleSelect.locator("option[value=true_cyoa]"),
  ).toHaveJSProperty("disabled", true);
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

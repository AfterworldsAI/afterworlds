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
  // FREEFORM_ONLY: the orchestrator's True CYOA INTERACTION_REJECTED gate
  // (see the sibling test below) only fires for TRUE_CYOA, so freeform
  // input here always reaches the ordinary prose Writer path regardless of
  // play_status.
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

test("Branching mode: True CYOA setup rejects freeform input", async ({
  page,
}) => {
  // Round 7 remediation (PR #126 P1): Branching setup now durably promotes
  // play_status to IN_PLAY once interaction_style + branching_cadence are
  // both persisted, so the orchestrator's True CYOA INTERACTION_REJECTED
  // gate -- always part of orchestrate_turn's core dispatch, not a
  // mode-specific pass service -- is reachable through the real setup
  // route. Before that fix, play_status could never reach IN_PLAY here, so
  // this freeform input fell through to the ordinary prose Writer and
  // rendered as an ordinary delivered turn instead of a rejection.
  seedEntitlement();

  await page.goto("/");
  await page.getByPlaceholder("Title").fill("A True CYOA Story");
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

  await expect(page.getByRole("alert")).toContainText(
    "True CYOA mode requires explicit branch selection",
  );
  // Rejected input is never delivered/ooc_handled, so the draft is
  // preserved, not cleared (Binding Decision 6).
  await expect(textarea).toHaveValue(
    "I ignore the options and climb the wall.",
  );
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

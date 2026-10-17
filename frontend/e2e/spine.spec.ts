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
  await page.getByRole("combobox").selectOption("branching");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
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

test("v1 new-story flow offers only Branching and RPG; Writing is refused (ADR-017b)", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const modeSelect = page.getByRole("combobox");
  await expect(modeSelect).toHaveValue("branching");
  await expect(modeSelect.locator("option")).toHaveText(["Branching", "RPG"]);

  // The untouched default submits a supported mode.
  await page.getByPlaceholder("Title").fill("Default Mode Story");
  await page.getByRole("button", { name: "Create" }).click();
  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Choose your Writing companion" }),
  ).toHaveCount(0);

  // Bypassing the UI: a direct Writing create gets the typed refusal and
  // creates nothing; the persona gallery offers nothing selectable.
  const refused = await request.post("/api/stories", {
    data: { title: "Direct Writing Story", mode: "writing" },
  });
  expect(refused.status()).toBe(422);
  expect((await refused.json()).error_code).toBe("mode_unavailable");
  const stories = (await (await request.get("/api/stories")).json()).stories;
  expect(
    stories.some((s: { title: string }) => s.title === "Direct Writing Story"),
  ).toBe(false);
  const personas = await (await request.get("/api/personas")).json();
  expect(personas.mentors).toEqual([]);
  expect(personas.peers).toEqual([]);
});

test("Branching mode: setup and a delivered turn", async ({ page }) => {
  // FREEFORM_ONLY: before Begin story this is a setup-confirmation turn on
  // the ordinary prose Writer path (ADR-016 Decision 3, ADR-016b).
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

test("Branching mode: card styles are selectable and Begin story opens with cards", async ({
  page,
}) => {
  // CRD Issue 21 Prerequisite A (ADR-016b): the Branching writer is wired,
  // setup only saves, and the separate Begin story control generates the
  // opening and its first cards. The fake provider's fixed classifier can't
  // express a selection; selection and True CYOA proofs run on the
  // production resolver in crd21-spine.spec.ts.
  seedEntitlement();

  await page.goto("/");
  await page.getByPlaceholder("Title").fill("A Hybrid Story");
  await page.getByRole("combobox").selectOption("branching");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
  const interactionStyleSelect = page.locator("select").first();
  await expect(interactionStyleSelect).toHaveValue("freeform_only");
  await expect(
    interactionStyleSelect.locator("option[value=true_cyoa]"),
  ).toHaveJSProperty("disabled", false);
  await interactionStyleSelect.selectOption("hybrid");
  await page.getByLabel("Branch options per beat").selectOption("2-3");
  await page.getByRole("button", { name: "Save setup" }).click();

  await page.getByRole("button", { name: "Begin story" }).click();
  await expect(
    page.getByText("The story branches, faked for E2E."),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Fake path 2" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Fake path 2" })).toBeVisible();
});

test("refresh/reload re-derives state from the API, not invented client state", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByPlaceholder("Title").fill("Reload Test Story");
  await page.getByRole("combobox").selectOption("branching");
  await page.getByRole("button", { name: "Create" }).click();
  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();

  const url = page.url();
  await page.reload();
  expect(page.url()).toBe(url);
  // Story detail, mode, and setup status are re-fetched, not reconstructed
  // from any client-held state.
  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
});

test("story selection persists the last-selected story across a full app reload", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByPlaceholder("Title").fill("Resume Story");
  await page.getByRole("combobox").selectOption("branching");
  await page.getByRole("button", { name: "Create" }).click();
  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();

  await page.goto("/");
  // last-selected story_id (permitted localStorage) routes back into it,
  // not the story list.
  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
});

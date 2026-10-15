import {
  expect,
  test,
  type APIRequestContext,
  type Page,
  type Request,
} from "@playwright/test";

/**
 * CRD Issue 19b through the BUILT app and the real API: the RPG dice server
 * (scripts/e2e_rpg_server.py) serves frontend/dist on a published-release
 * store with the fake provider. Only the GameMaster's proposals are scripted
 * (one action per story, queued by the e2e-only seed route); adjudication,
 * the action-resolution lifecycle, validation, locks and narration are the
 * production ones.
 *
 * Browser dice are made deterministic test-side by replacing
 * crypto.getRandomValues in the page -- the product has no test hook.
 */

type Scenario = "dagger" | "contest";

async function openRpgStory(
  page: Page,
  request: APIRequestContext,
  scenario: Scenario,
): Promise<string> {
  const title = `Dice ${scenario} ${Date.now()}`;
  const created = await request.post("/api/stories", {
    data: { title, mode: "rpg", character_name: "Ilse", schema_version: 1 },
  });
  expect(created.status()).toBe(201);
  const storyId = (await created.json()).story_id as string;
  const seeded = await request.post(`/__e2e__/rpg/${storyId}/${scenario}`);
  expect(seeded.ok()).toBeTruthy();
  await page.goto("/");
  await page.getByRole("button", { name: new RegExp(`^${title}`) }).click();
  await expect(page.getByPlaceholder("What do you do?")).toBeVisible();
  return storyId;
}

async function announce(page: Page, text: string) {
  await page.getByPlaceholder("What do you do?").fill(text);
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await expect(page.getByText("faked for E2E testing").first()).toBeVisible();
}

async function scriptDice(page: Page) {
  await page.addInitScript(() => {
    const faces: number[] = [];
    (window as unknown as { __faces: number[] }).__faces = faces;
    const real = crypto.getRandomValues.bind(crypto);
    crypto.getRandomValues = (<T extends ArrayBufferView | null>(
      array: T,
    ): T => {
      if (faces.length > 0 && array instanceof Uint32Array) {
        // A word below every die's rejection limit maps to face = word + 1.
        for (let i = 0; i < array.length; i++) array[i] = faces.shift()! - 1;
        return array;
      }
      return real(array);
    }) as typeof crypto.getRandomValues;
  });
}

async function nextFaces(page: Page, ...faces: number[]) {
  await page.evaluate((f) => {
    (window as unknown as { __faces: number[] }).__faces.push(...f);
  }, faces);
}

function rollBodies(page: Page): unknown[] {
  const bodies: unknown[] = [];
  page.on("request", (r: Request) => {
    if (r.method() === "POST" && r.url().endsWith("/rpg/rolls")) {
      bodies.push(r.postDataJSON());
    }
  });
  return bodies;
}

const pendingAction = (page: Page) =>
  page.getByRole("region", { name: "Pending action" });
const preview = (page: Page) =>
  page.getByRole("group", { name: "Roll preview" });
const UUID = expect.stringMatching(/^[0-9a-f-]{36}$/);

test("a linked dagger action: adjustment, digital dice, physical entry, decision and immediate narration", async ({
  page,
  request,
}) => {
  await scriptDice(page);
  const bodies = rollBodies(page);
  const resumes: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/resume")) resumes.push(r.url());
  });
  await openRpgStory(page, request, "dagger");
  await announce(page, "I stab the wolf.");

  const action = pendingAction(page);
  await expect(
    action.getByText("Roll needed: Dagger attack (1d20 + 1)"),
  ).toBeVisible();
  await expect(action.getByText(/^Step 1\b/)).toBeVisible();

  // An ordinary in-character action is held by the backend; the play view
  // takes the Sojourner to the roll and keeps the draft.
  await page.getByPlaceholder("What do you do?").fill("I run away.");
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await expect(page.getByRole("alert").first()).toContainText("Roll needed");
  await expect(action.locator("..")).toBeFocused();
  await expect(page.getByPlaceholder("What do you do?")).toHaveValue(
    "I run away.",
  );

  // A candidate for revision 1, then the offered adjustment: the revised
  // instruction replaces it before any new roll.
  await nextFaces(page, 3);
  await action.getByRole("button", { name: "Roll dice" }).click();
  await expect(preview(page).getByText("Preview total: 4")).toBeVisible();
  await expect(preview(page).locator(".dice-face").first()).toHaveCSS(
    "animation-name",
    "dice-tumble",
  );
  await action
    .getByRole("button", { name: "Use Dexterity instead (Finesse)" })
    .click();
  await expect(
    action.getByText("Roll needed: Dagger attack (1d20 + 4)"),
  ).toBeVisible();
  await expect(preview(page)).toHaveCount(0);
  expect(bodies).toHaveLength(0);

  await nextFaces(page, 15);
  await action.getByRole("button", { name: "Roll dice" }).click();
  await expect(preview(page).locator(".dice-face")).toHaveText(["15"]);
  await expect(preview(page).getByText("Preview total: 19")).toBeVisible();
  await expect(preview(page).getByText(/Unsubmitted preview/)).toBeVisible();
  await action.getByRole("button", { name: "Submit digital roll" }).click();

  await expect(action.getByText(/Roll needed: .*\(1d4 \+ 2\)/)).toBeVisible();
  await expect(action.getByText(/^Step 2\b/)).toBeVisible();
  expect(bodies).toEqual([
    {
      schema_version: 1,
      source: "inline_ui",
      pending_roll_request_id: UUID,
      expected_instruction_revision: 2,
      term_results: [{ schema_version: 1, term_id: UUID, values: [15] }],
    },
  ]);

  // Physical entry: malformed faces never reach the API.
  const faces = action.getByLabel(/faces rolled/);
  const submitPhysical = action.getByRole("button", {
    name: "Submit physical roll",
  });
  for (const [value, message] of [
    ["3.0", "Enter whole numbers only."],
    ["0x3", "Enter whole numbers only."],
    ["3 1", "Enter exactly 1 face."],
    ["5", "Each face must be from 1 to 4."],
  ]) {
    await faces.fill(value);
    await expect(action.getByText(message)).toBeVisible();
    await expect(submitPhysical).toBeDisabled();
  }
  expect(bodies).toHaveLength(1);
  await faces.fill("3");
  await submitPhysical.click();

  // 5 damage drops the 4-HP wolf: the stored knockout decision.
  await expect(action.getByText(/Knock it out instead\?/)).toBeVisible();
  expect(bodies[1]).toMatchObject({
    source: "physical_self_report",
    term_results: [{ values: [3] }],
  });
  expect(resumes).toHaveLength(0);
  await action.getByRole("button", { name: /^Knock it out/ }).click();

  // Ready: narrated at once, exactly once.
  await expect(pendingAction(page)).toHaveCount(0);
  await expect(page.getByText("faked for E2E testing")).toHaveCount(2);
  expect(resumes).toHaveLength(1);
  // Nothing about the roll was persisted in the browser.
  const stored = await page.evaluate(() => JSON.stringify({ ...localStorage }));
  expect(stored).not.toMatch(/term|values|inline_ui|pending/);
});

test("an uncertain or failed roll submission re-reads the backend: no replay, no re-roll", async ({
  page,
  request,
}) => {
  await scriptDice(page);
  await openRpgStory(page, request, "dagger");
  await announce(page, "I stab the wolf.");
  const action = pendingAction(page);

  // The server commits the roll but its response is lost.
  let delivered = 0;
  await page.route("**/rpg/rolls", async (route) => {
    await route.fetch();
    delivered++;
    await route.abort("connectionreset");
  });
  await nextFaces(page, 15);
  await action.getByRole("button", { name: "Roll dice" }).click();
  await action.getByRole("button", { name: "Submit digital roll" }).click();
  await expect(page.getByRole("alert").first()).toBeVisible();
  // The re-read shows what the backend holds: the damage roll.
  await expect(action.getByText(/Roll needed: .*\(1d4 - 1\)/)).toBeVisible();
  await expect(action.getByRole("button", { name: "Roll dice" })).toBeEnabled();
  expect(delivered).toBe(1);

  // A failure before the server: same step, same candidate, no POST
  // repeated by the client; only a deliberate resubmission goes out.
  await page.unroute("**/rpg/rolls");
  let failed = 0;
  await page.route("**/rpg/rolls", async (route) => {
    failed++;
    await route.abort("connectionrefused");
  });
  await nextFaces(page, 2);
  await action.getByRole("button", { name: "Roll dice" }).click();
  await expect(preview(page).locator(".dice-face")).toHaveText(["2"]);
  await action.getByRole("button", { name: "Submit digital roll" }).click();
  await expect(page.getByRole("alert").first()).toBeVisible();
  await expect(
    action.getByRole("button", { name: "Submit digital roll" }),
  ).toBeEnabled();
  await expect(preview(page).locator(".dice-face")).toHaveText(["2"]);
  await expect(action.getByText(/Roll needed: .*\(1d4 - 1\)/)).toBeVisible();
  expect(failed).toBe(1);

  await page.unroute("**/rpg/rolls");
  await action.getByRole("button", { name: "Submit digital roll" }).click();
  // 1 damage leaves the 4-HP wolf standing: ready, narrated at once.
  await expect(pendingAction(page)).toHaveCount(0);
  await expect(page.getByText("faked for E2E testing")).toHaveCount(2);
});

test("a stale revision from another tab is refused and re-read, discarding the candidate", async ({
  page,
  context,
  request,
}) => {
  await scriptDice(page);
  await openRpgStory(page, request, "dagger");
  await announce(page, "I stab the wolf.");

  const other = await context.newPage();
  await other.goto("/"); // same browser storage: the last-selected story
  await nextFaces(page, 11);
  await pendingAction(page).getByRole("button", { name: "Roll dice" }).click();
  await expect(preview(page).locator(".dice-face")).toHaveText(["11"]);

  await pendingAction(other)
    .getByRole("button", { name: "Use Dexterity instead (Finesse)" })
    .click();
  await expect(
    pendingAction(other).getByText("Roll needed: Dagger attack (1d20 + 4)"),
  ).toBeVisible();

  const bodies = rollBodies(page);
  await pendingAction(page)
    .getByRole("button", { name: "Submit digital roll" })
    .click();
  await expect(page.getByRole("alert").first()).toContainText(
    "The roll instruction has changed",
  );
  await expect(
    pendingAction(page).getByText("Roll needed: Dagger attack (1d20 + 4)"),
  ).toBeVisible();
  await expect(preview(page)).toHaveCount(0);
  await expect(
    pendingAction(page).getByRole("button", { name: "Roll dice" }),
  ).toBeEnabled();
  expect(bodies).toHaveLength(1);
  expect(bodies[0]).toMatchObject({ expected_instruction_revision: 1 });
});

test("ready after a failed narration: explicit resume on reload, and a completed resume elsewhere is success", async ({
  page,
  context,
  request,
}) => {
  await openRpgStory(page, request, "dagger");
  await announce(page, "I stab the wolf.");
  const action = pendingAction(page);

  // The immediate narration fails in transit; the recorded mechanics and
  // the ready affordance remain for a deliberate same-facts resume.
  await page.route("**/resume", (route) => route.abort("connectionrefused"));
  await action.getByLabel(/faces rolled/).fill("15");
  await action.getByRole("button", { name: "Submit physical roll" }).click();
  await action.getByLabel(/faces rolled/).fill("1");
  await action.getByRole("button", { name: "Submit physical roll" }).click();
  await expect(page.getByRole("alert").first()).toBeVisible();
  const narrate = action.getByRole("button", {
    name: "Narrate the resolved action",
  });
  await expect(narrate).toBeEnabled();
  await page.unroute("**/resume");

  const resumes: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/resume")) resumes.push(r.url());
  });
  await page.reload();
  await expect(narrate).toBeVisible();
  await expect(page.getByRole("button", { name: "Roll dice" })).toHaveCount(0);
  expect(resumes).toHaveLength(0); // never resumed by a reload

  const other = await context.newPage();
  await other.goto("/");
  const otherNarrate = pendingAction(other).getByRole("button", {
    name: "Narrate the resolved action",
  });
  await expect(otherNarrate).toBeVisible();

  await narrate.click();
  await expect(pendingAction(page)).toHaveCount(0);
  await expect(page.getByText("faked for E2E testing")).toHaveCount(2);

  // The other tab's resume finds the action narrated: no error, a refetch.
  await otherNarrate.click();
  await expect(pendingAction(other)).toHaveCount(0);
  await expect(other.getByText("faked for E2E testing")).toHaveCount(2);
  await expect(other.getByRole("alert")).toHaveCount(0);
});

test.describe("reduced motion", () => {
  test("an opposed check against a hidden counterpart is an ordinary roll on the same surface", async ({
    page,
    request,
  }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await scriptDice(page);
    const bodies = rollBodies(page);
    await openRpgStory(page, request, "contest");
    await announce(page, "I challenge the ape.");

    const action = pendingAction(page);
    await expect(
      action.getByText(/^Roll needed: .*\(1d20 - 1\)$/),
    ).toBeVisible();
    // The backend projects an ordinary check: nothing of the Ape, its
    // hidden roll or a target reaches the surface.
    await expect(action).not.toContainText(
      /\bape\b|counterpart|\bDC\b|hidden/i,
    );

    await nextFaces(page, 12);
    await action.getByRole("button", { name: "Roll dice" }).click();
    const face = preview(page).locator(".dice-face");
    await expect(face).toHaveText(["12"]);
    await expect(face).toHaveCSS("animation-name", "none");
    await expect(preview(page).getByText("Preview total: 11")).toBeVisible();
    await action.getByRole("button", { name: "Submit digital roll" }).click();

    await expect(pendingAction(page)).toHaveCount(0);
    await expect(page.getByText("faked for E2E testing")).toHaveCount(2);
    expect(bodies).toEqual([
      expect.objectContaining({
        source: "inline_ui",
        term_results: [{ schema_version: 1, term_id: UUID, values: [12] }],
      }),
    ]);
  });
});

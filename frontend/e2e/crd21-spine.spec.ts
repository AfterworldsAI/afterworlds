import {
  expect,
  test,
  type APIRequestContext,
  type Page,
} from "@playwright/test";

/**
 * CRD Issue 21 narrative spine against the BUILT app served by
 * scripts/e2e_spine_server.py: the production provider resolver, readiness
 * and binding (no fake provider), a published-release store, and only the
 * provider HTTP transport and credential storage replaced. Serial: one
 * server, one Sojourner. Hosted runs first; the BYOK half then adds a key,
 * so the existing BYOK-first selection takes over.
 */

const BYOK_KEY = "sk-ant-SYNTHETIC-e2e-byok-0123456789"; // pragma: allowlist secret
const N = 10; // ROLLING_SUMMARY_N (provisional, ADR-0009/ADR-006b)

test.describe.configure({ mode: "serial" });

type Call = { pass_name: string; path: string; texts: string[] };

async function calls(request: APIRequestContext): Promise<Call[]> {
  return (await (
    await request.get("/__e2e__/provider/calls")
  ).json()) as Call[];
}

async function push(
  request: APIRequestContext,
  pass: string,
  reply: Record<string, unknown>,
) {
  expect(
    (await request.post(`/__e2e__/provider/${pass}`, { data: reply })).ok(),
  ).toBe(true);
}

async function createStory(
  page: Page,
  title: string,
  mode: "branching" | "rpg",
) {
  await page.goto("/");
  const back = page.getByRole("button", { name: "Back to stories" });
  if (await back.isVisible()) await back.click();
  await page.getByPlaceholder("Title").fill(title);
  await page.getByRole("combobox").selectOption(mode);
  if (mode === "rpg")
    await page.getByPlaceholder("Character name").fill("Ilse");
  await page.getByRole("button", { name: "Create" }).click();
  // The new story is selected (and its id stored) once its setup shows.
  await expect(
    page.getByRole("heading", {
      name: mode === "rpg" ? "RPG setup" : "Branching setup",
    }),
  ).toBeVisible();
}

async function setupBranching(page: Page, style: string, range?: string) {
  await expect(
    page.getByRole("heading", { name: "Branching setup" }),
  ).toBeVisible();
  await page.getByLabel("Interaction style").selectOption(style);
  if (range)
    await page.getByLabel("Branch options per beat").selectOption(range);
  await page.getByRole("button", { name: "Save setup" }).click();
  await expect(page.getByRole("button", { name: "Begin story" })).toBeVisible();
}

function storyIdOf(page: Page): Promise<string> {
  return page.evaluate(() => {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i) ?? "";
      if (/last.*story/i.test(key)) return localStorage.getItem(key) ?? "";
    }
    return "";
  });
}

const narration = (page: Page) => page.locator(".transcript-assistant-output");

test("Branching True CYOA on hosted: Begin, cards, selection, reload, Rolling Summary", async ({
  page,
  request,
}) => {
  expect((await request.post("/__e2e__/access/hosted")).ok()).toBe(true);
  await createStory(page, "Harbor of Cards", "branching");
  await setupBranching(page, "true_cyoa", "2-3");
  // Setup saved, nothing generated: reload restores the ready-to-begin state.
  await expect(page.getByText("No turns yet")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Begin story" })).toBeVisible();
  const before = (await calls(request)).length;

  await page.getByRole("button", { name: "Begin story" }).click();
  await expect(narration(page).first()).toHaveText(
    "The story opens on a rain-dark harbor at dusk.",
  );
  await expect(page.getByRole("button", { name: "Path 1" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Path 2" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Begin story" })).toHaveCount(
    0,
  );
  const opening = (await calls(request)).slice(before);
  expect(opening.map((c) => c.pass_name)).not.toContain("intent_classifier");
  expect(opening.map((c) => c.pass_name)).toContain("branching_writer");
  expect(new Set(opening.map((c) => c.path))).toEqual(new Set(["hosted"]));

  // True CYOA refuses freeform input; nothing is generated or billed.
  const textarea = page.getByPlaceholder(/Choose a branch card/);
  await textarea.fill("I climb the harbor wall.");
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "True CYOA mode requires explicit branch selection",
  );
  await expect(textarea).toHaveValue("I climb the harbor wall.");
  await textarea.fill("");

  // An explicit selection continues the story with new committed cards.
  await page.getByRole("button", { name: "Path 2" }).click();
  await expect(narration(page)).toHaveCount(2);
  await expect(narration(page).nth(1)).toContainText("I choose option 2");
  await page.reload();
  await expect(narration(page)).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Path 1" })).toBeVisible();

  // Eligible turns #3..#10: the tenth commits the first Rolling Summary.
  const storyId = await storyIdOf(page);
  for (let i = 3; i <= N; i++) {
    await page.getByRole("button", { name: "Path 1" }).click();
    await expect(narration(page)).toHaveCount(i);
  }
  const rows = await (
    await request.get(`/__e2e__/stories/${storyId}/summaries`)
  ).json();
  expect(rows).toHaveLength(1);
  expect(rows[0].version_number).toBe(1);
  const summaryCalls = (await calls(request)).filter(
    (c) => c.pass_name === "rolling_summary",
  );
  expect(summaryCalls).toHaveLength(1);
  expect(summaryCalls[0].path).toBe("hosted");
  const deductions = await (await request.get("/__e2e__/deductions")).json();
  expect(rows[0].compressed_through_turn_id in deductions).toBe(true);

  // The next turn's context carries the committed summary.
  await page.getByRole("button", { name: "Path 1" }).click();
  await expect(narration(page)).toHaveCount(N + 1);
  const planner = (await calls(request))
    .filter((c) => c.pass_name === "planner")
    .pop();
  expect(planner?.texts.some((t) => t.includes(rows[0].text))).toBe(true);
});

test("Branching Hybrid on hosted: a failed opening stays ready, unbilled and retryable", async ({
  page,
  request,
}) => {
  await createStory(page, "Storm Opening", "branching");
  await setupBranching(page, "hybrid", "1-2");
  const deductions = await (await request.get("/__e2e__/deductions")).json();
  await push(request, "branching_writer", { status: 500 });

  await page.getByRole("button", { name: "Begin story" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "branching writer pass failed",
  );
  await expect(page.getByText("No turns yet")).toBeVisible();
  await expect(page.getByRole("button", { name: "Begin story" })).toBeEnabled();
  expect(await (await request.get("/__e2e__/deductions")).json()).toEqual(
    deductions,
  );

  await page.getByRole("button", { name: "Begin story" }).click();
  await expect(narration(page)).toHaveCount(1);
  // Hybrid offers cards and freeform input together.
  await page.getByPlaceholder("What do you do?").fill("I hail the ferryman.");
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await expect(narration(page)).toHaveCount(2);
  await expect(page.getByRole("button", { name: "Path 1" })).toBeVisible();
});

// Setup -> separate Begin -> opening -> next interaction -> reload, for one
// fresh story of any style (ADR-016b acceptance proof).
async function playBranching(
  page: Page,
  request: APIRequestContext,
  style: "freeform_only" | "hybrid" | "true_cyoa",
): Promise<Call[]> {
  const before = (await calls(request)).length;
  await expect(page.getByText("No turns yet")).toBeVisible();
  await page.getByRole("button", { name: "Begin story" }).click();
  await expect(narration(page)).toHaveCount(1);
  if (style === "freeform_only") {
    await expect(page.locator(".branch-card")).toHaveCount(0);
    await page.getByPlaceholder("What do you do?").fill("I light the lantern.");
    await page.getByRole("button", { name: "Submit", exact: true }).click();
  } else {
    await page.getByRole("button", { name: "Path 1" }).click();
  }
  await expect(narration(page)).toHaveCount(2);
  await page.reload();
  await expect(narration(page)).toHaveCount(2);
  if (style !== "freeform_only") {
    await expect(page.getByRole("button", { name: "Path 1" })).toBeVisible();
  }
  return (await calls(request)).slice(before);
}

async function rpgTurn(
  page: Page,
  request: APIRequestContext,
  visibility: string,
) {
  await push(request, "rpg_adjudication", {
    tool_input: {
      rolls: [
        {
          check_label: "Athletics Check",
          subsystem_tag: "climb",
          visibility,
          operation: "fixed_dc_check",
          check_identity: "glossary.climbing/difficult_climb",
        },
      ],
    },
  });
  const count = await narration(page).count();
  await page
    .getByPlaceholder("What do you do?")
    .fill("I climb the rain-slick wall.");
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await expect(narration(page)).toHaveCount(count + 1);
}

test("Branching Freeform-only on hosted: Begin, opening, next turn, reload", async ({
  page,
  request,
}) => {
  await createStory(page, "Open Water", "branching");
  await setupBranching(page, "freeform_only");
  const used = await playBranching(page, request, "freeform_only");
  expect(used.map((c) => c.pass_name)).not.toContain("branching_writer");
  expect(new Set(used.map((c) => c.path))).toEqual(new Set(["hosted"]));
});

// ADR-015c: a fresh RPG story through the product's pre-play sequence --
// world (after a GM clarification), confirmed; a Rules Package selected; a
// character from the GM conversation (after a clarification) or a pasted
// sheet (first reviewed with an unresolved problem), accepted; configuration
// saved, summarized by the GM and that summary confirmed -- with reloads
// along the way. Nothing seeds character state.
async function rpgStartup(
  page: Page,
  request: APIRequestContext,
  title: string,
  path: "gm_led" | "completed_sheet",
  dice: "ai_rolls" | "player_rolls",
) {
  await createStory(page, title, "rpg");
  await expect(page.getByTestId("rpg-setup-phase")).toContainText("world");
  const composer = page.getByPlaceholder("What do you do?");
  const say = async (text: string) => {
    await composer.fill(text);
    await page.getByRole("button", { name: "Submit", exact: true }).click();
  };
  const envelope = (gm_text: string, result: Record<string, unknown>) => ({
    tool_input: { schema_version: 1, gm_text, result },
  });

  // World: a clarification offers nothing to confirm.
  await push(
    request,
    "rpg_setup_writer",
    envelope("Who rules the northern isles?", {
      kind: "clarification",
      questions: ["Who rules the northern isles?"],
    }),
  );
  await say("A storm-wracked archipelago of lighthouses.");
  await expect(narration(page).last()).toContainText("northern isles");
  await expect(page.getByRole("button", { name: "Confirm world" })).toHaveCount(
    0,
  );
  await say("The lighthouse guilds rule every isle.");
  await expect(page.getByText(/GM understanding/)).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Confirm world" }).click();
  await expect(page.getByTestId("rpg-setup-phase")).toContainText("character");

  await page.getByRole("button", { name: "Use this Rules Package" }).click();
  await expect(page.getByText("Selected.")).toBeVisible();
  const character = await (
    await request.get("/__e2e__/fixtures/character")
  ).json();
  const proposal = (unresolved: string[]) =>
    envelope("Here is your character as I have it.", {
      kind: "character_proposal",
      path,
      character,
      unresolved,
    });
  const accept = page.getByRole("button", { name: "Accept character" });
  if (path === "gm_led") {
    // The scripted GM's default character-creation reply is a clarification.
    await say("A wizard with a sage background.");
    // The first authority read on a fresh server warms its index (slow).
    await expect(narration(page).last()).toContainText("sage background", {
      timeout: 120_000,
    });
    await expect(page.getByText(/Character for review/)).toHaveCount(0);
    await push(request, "rpg_setup_writer", proposal([]));
    await say("Standard array, please.");
  } else {
    await push(request, "rpg_setup_writer", proposal(["Which cantrips?"]));
    const sheet = page.getByLabel("Completed character sheet");
    await sheet.fill(
      "Wizard 1 / Elf / Sage / Str 8 Dex 14 Con 13 Int 15 Wis 12 Cha 10",
    );
    await page.getByRole("button", { name: "Submit sheet" }).click();
    // The first authority read on a fresh server warms its index (slow).
    await expect(page.getByLabel("Outstanding problems")).toContainText(
      "Which cantrips?",
      { timeout: 120_000 },
    );
    await expect(sheet).toHaveValue("");
    await expect(accept).toBeDisabled();
    await push(request, "rpg_setup_writer", proposal([]));
    await say("Fire Bolt and Light.");
    await expect(page.getByLabel("Outstanding problems")).toHaveCount(0);
  }
  await expect(page.getByText(/Character for review/)).toBeVisible({
    timeout: 120_000,
  });
  await page.reload();
  await expect(accept).toBeEnabled();
  await accept.click();
  await expect(page.getByTestId("rpg-setup-phase")).toContainText(
    "play configuration",
  );

  // Configuration: saved, summarized by the GM, then exactly that confirmed.
  await page.reload();
  const complete = page.getByRole("button", { name: "Complete setup" });
  await expect(complete).toHaveCount(0);
  await page.getByLabel("Dice handling").selectOption(dice);
  await page.getByLabel("Tone").selectOption("gritty");
  await page.getByRole("button", { name: "Save configuration" }).click();
  await expect(page.getByText(/Ask the GM below to summarize/)).toBeVisible();
  await say("Please confirm my settings.");
  const summary = page.getByText(/GM summary to confirm/);
  await expect(summary).toContainText("Please confirm my settings.");
  // The scripted GM names the saved values it was shown.
  await expect(summary).toContainText("tone: gritty");
  await expect(summary).toContainText(`dice_handling: ${dice}`);
  await page.reload();
  await complete.click();
  await expect(page.locator(".rpg-visible-state")).toContainText("Ilse");
  await expect(page.getByTestId("rpg-setup-phase")).toHaveCount(0);
  await page.reload();
  await expect(page.locator(".rpg-visible-state")).toContainText("Ilse");
  const setup = await (
    await request.get(`/api/stories/${await storyIdOf(page)}/setup`)
  ).json();
  expect(setup.setup_state).toMatchObject({
    dice_handling: dice,
    tone: "gritty",
  });
}

// A player-rolled check: the roll is entered in the app, and the ready
// action is narrated through the ordinary resume turn.
async function rpgPlayerRoll(page: Page, request: APIRequestContext) {
  await push(request, "rpg_adjudication", {
    tool_input: {
      rolls: [
        {
          check_label: "Athletics Check",
          subsystem_tag: "climb",
          visibility: "shown",
          operation: "fixed_dc_check",
          check_identity: "glossary.climbing/difficult_climb",
        },
      ],
    },
  });
  const count = await narration(page).count();
  await page.getByPlaceholder("What do you do?").fill("I climb the wet wall.");
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await expect(narration(page)).toHaveCount(count + 1);
  await page.getByRole("button", { name: "Roll dice" }).click();
  await page.getByRole("button", { name: "Submit digital roll" }).click();
  await expect(narration(page)).toHaveCount(count + 2);
  await page.reload();
  await expect(narration(page)).toHaveCount(count + 2);
}

test("RPG on hosted: GM-led creation, player roll and resume", async ({
  page,
  request,
}) => {
  const before = (await calls(request)).length;
  await rpgStartup(page, request, "Wet Stone", "gm_led", "player_rolls");
  await rpgPlayerRoll(page, request);
  const used = (await calls(request)).slice(before);
  expect(used.map((c) => c.pass_name)).toContain("rpg_setup_writer");
  expect(used.map((c) => c.pass_name)).toContain("rpg_adjudication");
  expect(new Set(used.map((c) => c.path))).toEqual(new Set(["hosted"]));
});

test("RPG on hosted: completed-sheet entry, then backend checks", async ({
  page,
  request,
}) => {
  await rpgStartup(page, request, "Dry Stone", "completed_sheet", "ai_rolls");
  await rpgTurn(page, request, "shown");
  await rpgTurn(page, request, "hidden");
  await expect(page.locator("body")).not.toContainText("Athletics");
  await page.reload();
  await expect(page.locator(".rpg-visible-state")).toContainText("Ilse");
  await expect(page.locator("body")).not.toContainText("Athletics");
});

test("BYOK: a key saved in the app takes over Branching and RPG with no hosted deduction", async ({
  page,
  request,
}) => {
  expect((await request.post("/__e2e__/access/byok")).ok()).toBe(true);
  await page.goto("/");
  await page.getByRole("button", { name: "Account & BYOK" }).click();
  await page.getByLabel("Anthropic API key").fill(BYOK_KEY);
  await page.getByRole("button", { name: "Save Anthropic key" }).click();
  await expect(page.getByTestId("selected-access-path")).toContainText(/BYOK/i);
  expect(await page.content()).not.toContain(BYOK_KEY);
  await page.getByRole("button", { name: "Close account" }).click();

  const deductions = await (await request.get("/__e2e__/deductions")).json();
  const before = (await calls(request)).length;

  await createStory(page, "Private Lanterns", "branching");
  await setupBranching(page, "freeform_only");
  await playBranching(page, request, "freeform_only");

  // Hybrid, saved partially (no range yet; ADR-016b allows it): a reload
  // restores the hydrated form, not a Begin the server would refuse.
  await createStory(page, "Private Bridges", "branching");
  const hybridId = await storyIdOf(page);
  const partial = await request.post(`/api/stories/${hybridId}/setup`, {
    data: {
      mode: "branching",
      interaction_style: "hybrid",
      branching_cadence: "immersive",
    },
  });
  expect(partial.ok()).toBe(true);
  await page.reload();
  await expect(page.getByLabel("Interaction style")).toHaveValue("hybrid");
  await expect(page.getByLabel("Cadence")).toHaveValue("immersive");
  await expect(page.getByRole("button", { name: "Begin story" })).toHaveCount(
    0,
  );
  await page.getByLabel("Branch options per beat").selectOption("2-3");
  await page.getByRole("button", { name: "Save setup" }).click();
  await playBranching(page, request, "hybrid");

  await createStory(page, "Private Choices", "branching");
  await setupBranching(page, "true_cyoa", "2-4");
  await playBranching(page, request, "true_cyoa");

  // RPG through the product startup, both character paths, on BYOK.
  await rpgStartup(page, request, "Private Stone", "gm_led", "ai_rolls");
  await rpgTurn(page, request, "shown");
  await rpgStartup(
    page,
    request,
    "Private Glass",
    "completed_sheet",
    "player_rolls",
  );
  await rpgPlayerRoll(page, request);

  const used = (await calls(request)).slice(before);
  expect(used.length).toBeGreaterThan(0);
  expect(new Set(used.map((c) => c.path))).toEqual(new Set(["byok"]));
  expect(await (await request.get("/__e2e__/deductions")).json()).toEqual(
    deductions,
  );
});

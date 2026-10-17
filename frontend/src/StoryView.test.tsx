import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "./api/client";
import type {
  RpgSetupView,
  StoryDetail,
  TurnSubmissionResponse,
  VisibleState,
} from "./api/client";
import SetupForm, { WritingSetupForm } from "./SetupForm";
import StoryView from "./StoryView";

const baseStory: StoryDetail = {
  story_id: "11111111-1111-1111-1111-111111111111",
  title: "Test Story",
  mode: "branching",
  status: "in_play",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  schema_version: 1,
};

function rpgSetupView(overrides: Partial<RpgSetupView> = {}): RpgSetupView {
  return {
    phase: "world_setup",
    play_status: "setup",
    world_revision: 0,
    world_target: null,
    packages: [],
    selected_package_uuid: null,
    candidate: null,
    character_accepted: false,
    configuration_revision: 0,
    configuration_target: null,
    configuration: {
      dice_handling: "ai_rolls",
      gm_cheating: true,
      tone: "balanced",
      session_type: "open_ended",
      genre_flavor: null,
      house_rules: null,
      acceptable_content: null,
      schema_version: 1,
    },
    schema_version: 1,
    ...overrides,
  };
}

function deliveredResponse(): TurnSubmissionResponse {
  return {
    disposition: "delivered",
    turn_id: "22222222-2222-2222-2222-222222222222",
    delivered_output: "ok",
    stable_prefix_cache_warmed: false,
    interaction_rejection_reason: null,
    interaction_rejection_message: null,
    pipeline_error_summary: null,
    provider_refusal: null,
    pending_roll_redirect_message: null,
    settlement_warning: null,
    visible_state: null,
    schema_version: 1,
  };
}

function branchingVisibleState(): VisibleState {
  return {
    schema_version: 1,
    interaction_style: "hybrid",
    branching_cadence: "balanced",
    branch_count_range: "2-3",
    freeform_available: true,
    length_preference: null,
  };
}

function writingVisibleState(): VisibleState {
  return {
    schema_version: 1,
    story_id: "11111111-1111-1111-1111-111111111111",
    persona_id: "chiron",
    persona_display_name: "Chiron",
    relationship_orientation: "mentor",
    ui_short_description: "Patient mentor.",
    ui_long_description: "Chiron approaches every project methodically.",
    signature_move: "Progressive challenge",
    demeanor_tags: ["patient"],
    play_status: "in_play",
    specific_goals: "Draft the opening chapter of a mystery novel",
    reading_interests: null,
    writing_interests: null,
    critique_intensity: "balanced",
    form: null,
    form_other: null,
    tense: null,
    pov: null,
    style_density: "balanced",
    dialogue_narration_ratio: null,
    genre_conventions: null,
    beat_constraints: [],
    version_pointers: [],
    acceptable_content: null,
  };
}

function pipelineErrorResponse(): TurnSubmissionResponse {
  return {
    disposition: "pipeline_error",
    turn_id: null,
    delivered_output: null,
    stable_prefix_cache_warmed: false,
    interaction_rejection_reason: null,
    interaction_rejection_message: null,
    pipeline_error_summary: "boom",
    provider_refusal: null,
    pending_roll_redirect_message: null,
    settlement_warning: null,
    visible_state: null,
    schema_version: 1,
  };
}

const mocks = vi.hoisted(() => ({
  getStory: vi.fn(),
  getLatestTranscript: vi.fn(),
  getVisibleState: vi.fn(),
  getSetupState: vi.fn(),
  submitTurn: vi.fn(),
  submitSetup: vi.fn(),
  listPersonas: vi.fn(),
  getPendingInteraction: vi.fn(),
  submitRoll: vi.fn(),
  applyAdjustment: vi.fn(),
  submitDecision: vi.fn(),
  resumeSequence: vi.fn(),
  beginStory: vi.fn(),
  getRpgSetup: vi.fn(),
  confirmWorld: vi.fn(),
  selectRulesPackage: vi.fn(),
  acceptCharacter: vi.fn(),
  completeRpgSetup: vi.fn(),
}));

vi.mock("./api/client", async () => {
  const actual =
    await vi.importActual<typeof import("./api/client")>("./api/client");
  return {
    ...actual,
    api: {
      getStory: mocks.getStory,
      getLatestTranscript: mocks.getLatestTranscript,
      getVisibleState: mocks.getVisibleState,
      getSetupState: mocks.getSetupState,
      submitTurn: mocks.submitTurn,
      submitSetup: mocks.submitSetup,
      listPersonas: mocks.listPersonas,
      getPendingInteraction: mocks.getPendingInteraction,
      beginStory: mocks.beginStory,
      getRpgSetup: mocks.getRpgSetup,
      confirmWorld: mocks.confirmWorld,
      selectRulesPackage: mocks.selectRulesPackage,
      acceptCharacter: mocks.acceptCharacter,
      completeRpgSetup: mocks.completeRpgSetup,
      submitRoll: mocks.submitRoll,
      applyAdjustment: mocks.applyAdjustment,
      submitDecision: mocks.submitDecision,
      resumeSequence: mocks.resumeSequence,
    },
  };
});

describe("StoryView draft preservation (Binding Decision 6)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getStory.mockResolvedValue(baseStory);
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
    mocks.getSetupState.mockResolvedValue(null);
  });

  it("clears the draft only after a delivered turn", async () => {
    mocks.submitTurn.mockResolvedValue(deliveredResponse());
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => expect(textarea).toHaveValue(""));
  });

  it("reports a settled turn (CRD Issue 20 account refresh), not a refused one", async () => {
    const onTurnSettled = vi.fn();
    mocks.submitTurn
      .mockRejectedValueOnce(
        new ApiRequestError(403, {
          error_code: "entitlement_blocked",
          message: "No runnable access path for this Sojourner.",
          detail: null,
          schema_version: 1,
        }),
      )
      .mockResolvedValueOnce(deliveredResponse());
    render(
      <StoryView storyId={baseStory.story_id} onTurnSettled={onTurnSettled} />,
    );
    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));
    await screen.findByText(/No runnable access path/);
    expect(onTurnSettled).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /submit/i }));
    await waitFor(() => expect(textarea).toHaveValue(""));
    expect(onTurnSettled).toHaveBeenCalledTimes(1);
  });

  it("preserves the draft when the turn returns pipeline_error", async () => {
    mocks.submitTurn.mockResolvedValue(pipelineErrorResponse());
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("boom", { exact: false });
    expect(textarea).toHaveValue("hello there");
  });

  it("preserves the draft AND the play view on a transport/typed-error failure (e.g. 403 entitlement block)", async () => {
    mocks.submitTurn.mockRejectedValue(
      new ApiRequestError(403, {
        error_code: "entitlement_blocked",
        message: "No runnable access path for this Sojourner.",
        detail: null,
        schema_version: 1,
      }),
    );
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("No runnable access path for this Sojourner.");
    // The play view itself -- not a full-page error screen -- stays up.
    expect(textarea).toHaveValue("hello there");
    expect(screen.getByPlaceholderText("What do you do?")).toBeInTheDocument();
  });
});

describe("StoryView separates mutation success from refresh failure (PR #126 round 11)", () => {
  beforeEach(() => {
    localStorage.clear();
    // This suite asserts call counts, which the rest of this file's shared
    // vi.hoisted mocks don't reset between tests (mockClear() only clears
    // call history, not queued mockResolvedValueOnce values set per-test).
    vi.clearAllMocks();
    mocks.getStory.mockResolvedValue(baseStory);
    mocks.getVisibleState.mockResolvedValue(null);
    mocks.getSetupState.mockResolvedValue(null);
  });

  it("POST failure: draft remains, turnError is shown, lastResponse is not mutated", async () => {
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.submitTurn.mockRejectedValue(new Error("network down"));
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("network down");
    expect(textarea).toHaveValue("hello there");
    // The refresh path never runs: only the initial-load call happened.
    expect(mocks.getLatestTranscript).toHaveBeenCalledTimes(1);
  });

  it("POST succeeds, refresh succeeds: draft clears, transcript updates, no error", async () => {
    mocks.getLatestTranscript
      .mockResolvedValueOnce([]) // initial load
      .mockResolvedValueOnce([
        {
          turn_id: "t1",
          user_input: "hello there",
          assistant_output: "The story continues.",
          timestamp: "2026-01-01T00:00:00Z",
          intent_classification: "in_character_action",
          schema_version: 1,
        },
      ]);
    mocks.submitTurn.mockResolvedValue(deliveredResponse());
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("The story continues.");
    expect(textarea).toHaveValue("");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("POST succeeds, refresh fails: draft still clears for delivered, lastResponse/prior transcript are preserved, and the error is refresh-specific, not a submission failure", async () => {
    mocks.getLatestTranscript
      .mockResolvedValueOnce([
        {
          turn_id: "prior",
          user_input: "earlier input",
          assistant_output: "earlier output",
          timestamp: "2026-01-01T00:00:00Z",
          intent_classification: "in_character_action",
          schema_version: 1,
        },
      ]) // initial load
      .mockRejectedValueOnce(new Error("transcript fetch failed")); // post-submit refresh
    mocks.submitTurn.mockResolvedValue(deliveredResponse());
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByText("earlier output");

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("transcript fetch failed");
    // Draft clearing is driven by disposition (delivered), not by whether
    // the follow-up refresh succeeded.
    expect(textarea).toHaveValue("");
    // The prior transcript survives a failed refresh -- not wiped/reset.
    expect(screen.getByText("earlier output")).toBeInTheDocument();
    // Never phrased as a submission failure -- the turn already succeeded.
    expect(screen.queryByText(/submission failed/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/no runnable access path/i),
    ).not.toBeInTheDocument();
  });

  it("refresh-retry recovers without re-submitting the turn", async () => {
    mocks.getLatestTranscript
      .mockResolvedValueOnce([]) // initial load
      .mockRejectedValueOnce(new Error("transcript fetch failed")) // post-submit refresh
      .mockResolvedValueOnce([
        {
          turn_id: "t1",
          user_input: "hello there",
          assistant_output: "The story continues.",
          timestamp: "2026-01-01T00:00:00Z",
          intent_classification: "in_character_action",
          schema_version: 1,
        },
      ]); // retry
    mocks.submitTurn.mockResolvedValue(deliveredResponse());
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("transcript fetch failed");
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    await screen.findByText("The story continues.");
    expect(
      screen.queryByText("transcript fetch failed"),
    ).not.toBeInTheDocument();
    // Retrying the refresh must never re-submit the turn.
    expect(mocks.submitTurn).toHaveBeenCalledTimes(1);
  });

  it("sibling audit: a refresh failure after SetupForm's onComplete surfaces as refreshError, not an unhandled rejection", async () => {
    // SetupForm's submit() only calls onComplete() after api.submitSetup()
    // already succeeded -- the same "mutation success, follow-up read
    // fails" shape as submitTurn, previously uncaught (onComplete's
    // refresh() call was fire-and-forget with no catch of its own).
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "branching",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue(null);
    mocks.submitSetup.mockResolvedValue({});
    mocks.getLatestTranscript
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new Error("post-setup refresh failed"));

    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Branching setup" });
    // Save waits for the persisted setup to hydrate (ADR-016b partial setup).
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Save setup" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));

    await screen.findByText("post-setup refresh failed");
  });
});

// Retained Writing component proofs (ADR-017b): SetupForm no longer routes to
// WritingSetupForm in v1, so it is rendered directly here.
function renderWritingSetupForm() {
  render(
    <WritingSetupForm submitting={false} error={null} onSubmit={vi.fn()} />,
  );
}

describe("WritingSetupForm persona load (PR #126 round 13 P2)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a visible error and keeps Save disabled when the persona gallery fails to load", async () => {
    mocks.listPersonas.mockRejectedValue(new Error("network down"));
    renderWritingSetupForm();

    await screen.findByText(/Could not load Writing companions/i);
    // "Save setup" isn't reachable via an accessible name until goals are
    // filled and a persona is selectable, so query the raw submit button.
    const saveButton = screen
      .getByRole("heading", { name: "Choose your Writing companion" })
      .closest("form")
      ?.querySelector('button[type="submit"]');
    expect(saveButton).toBeDisabled();
  });

  it("retry reloads personas and clears the error without a page reload", async () => {
    mocks.listPersonas.mockRejectedValueOnce(new Error("network down"));
    renderWritingSetupForm();

    await screen.findByText(/Could not load Writing companions/i);

    mocks.listPersonas.mockResolvedValueOnce({
      mentors: [
        {
          persona_id: "chiron",
          display_name: "Chiron",
          orientation: "mentor",
          ui_short_description: "Patient mentor.",
          ui_long_description: "Chiron approaches every project methodically.",
          demeanor_tags: ["patient"],
          signature_move: "Progressive challenge",
          schema_version: 1,
        },
      ],
      peers: [],
    });
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    await screen.findByRole("button", { name: /Chiron/ });
    expect(
      screen.queryByText(/Could not load Writing companions/i),
    ).not.toBeInTheDocument();
  });

  it("successful load renders persona cards and allows selection, enabling Save once goals are filled", async () => {
    mocks.listPersonas.mockResolvedValue({
      mentors: [
        {
          persona_id: "chiron",
          display_name: "Chiron",
          orientation: "mentor",
          ui_short_description: "Patient mentor.",
          ui_long_description: "Chiron approaches every project methodically.",
          demeanor_tags: ["patient"],
          signature_move: "Progressive challenge",
          schema_version: 1,
        },
      ],
      peers: [],
    });
    renderWritingSetupForm();

    const personaButton = await screen.findByRole("button", { name: /Chiron/ });
    fireEvent.click(personaButton);
    fireEvent.change(
      screen.getByPlaceholderText(
        "e.g. Draft the opening chapter of a mystery novel",
      ),
      { target: { value: "Draft a short story." } },
    );

    expect(screen.getByRole("button", { name: "Save setup" })).toBeEnabled();
  });
});

describe("StoryView consumes turn-response visible_state before refresh (PR #126 round 14 P2)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    mocks.getStory.mockResolvedValue(baseStory);
    mocks.getSetupState.mockResolvedValue(null);
  });

  it("POST succeeds with a non-null visible_state, refresh fails: the returned visible state is shown", async () => {
    mocks.getVisibleState.mockResolvedValue(null); // initial load: no state yet
    mocks.getLatestTranscript
      .mockResolvedValueOnce([]) // initial load
      .mockRejectedValueOnce(new Error("transcript fetch failed")); // post-submit refresh
    mocks.submitTurn.mockResolvedValue({
      ...deliveredResponse(),
      visible_state: writingVisibleState(),
    });
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("transcript fetch failed");
    expect(screen.getByRole("heading", { name: "Chiron" })).toBeInTheDocument();
  });

  it("POST succeeds with visible_state: null, refresh fails: no stale state is invented", async () => {
    mocks.getVisibleState.mockResolvedValue(writingVisibleState()); // initial load: already has state
    mocks.getLatestTranscript
      .mockResolvedValueOnce([]) // initial load
      .mockRejectedValueOnce(new Error("transcript fetch failed")); // post-submit refresh
    mocks.submitTurn.mockResolvedValue({
      ...deliveredResponse(),
      visible_state: null,
    });
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Chiron" });
    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("transcript fetch failed");
    expect(
      screen.queryByRole("heading", { name: "Chiron" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("Complete setup to see story state here."),
    ).toBeInTheDocument();
  });

  it("POST succeeds and refresh succeeds: the follow-up read is the final state", async () => {
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.submitTurn.mockResolvedValue({
      ...deliveredResponse(),
      visible_state: {
        ...writingVisibleState(),
        persona_display_name: "ResponsePersona",
      },
    });
    mocks.getVisibleState.mockResolvedValueOnce(null); // initial load
    mocks.getVisibleState.mockResolvedValueOnce({
      ...writingVisibleState(),
      persona_display_name: "RefreshPersona",
    }); // post-submit refresh
    render(<StoryView storyId={baseStory.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByRole("heading", { name: "RefreshPersona" });
    expect(
      screen.queryByRole("heading", { name: "ResponsePersona" }),
    ).not.toBeInTheDocument();
  });

  it("POST failure does not mutate visible state", async () => {
    mocks.getVisibleState.mockResolvedValue(writingVisibleState());
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.submitTurn.mockRejectedValue(new Error("network down"));
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Chiron" });
    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello there" } });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));

    await screen.findByText("network down");
    expect(screen.getByRole("heading", { name: "Chiron" })).toBeInTheDocument();
  });
});

describe("StoryView setup handoff survives reload (PR #126 round 3)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.submitSetup.mockResolvedValue({});
    mocks.getSetupState.mockResolvedValue(null);
    mocks.listPersonas.mockResolvedValue({ mentors: [], peers: [] });
  });

  it("shows the play view (not SetupForm) for a Writing story with persisted nonblank specific_goals", async () => {
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "writing",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue(writingVisibleState());

    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByPlaceholderText("What do you do?");
    expect(
      screen.queryByRole("heading", { name: "Choose your Writing companion" }),
    ).not.toBeInTheDocument();
  });

  it("shows the play view even while play_status is still setup, once specific_goals is genuinely persisted (PR #126 round 13)", async () => {
    // Round 13 boundary decision: POST /setup no longer promotes
    // play_status itself (ADR-017 Decision 9 / ADR-018 D6 -- the story
    // stays SETUP until the setup-confirmation turn lands). A Sojourner who
    // reloads between completing setup and submitting that first turn must
    // still reach the play view, not bounce back to SetupForm -- checking
    // play_status here (as before round 13) would have reintroduced that
    // exact bounce.
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "writing",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue({
      ...writingVisibleState(),
      play_status: "setup",
    });

    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByPlaceholderText("What do you do?");
    expect(
      screen.queryByRole("heading", { name: "Choose your Writing companion" }),
    ).not.toBeInTheDocument();
  });

  it("shows the Writing-unavailable notice, not persona setup, for a Writing story still in setup (ADR-017b)", async () => {
    // A row with persona_id set but blank specific_goals stays on the setup
    // screen (PR #126 round 5 follow-up); in v1 that screen offers no
    // Writing or persona controls.
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "writing",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue({
      ...writingVisibleState(),
      play_status: "setup",
      specific_goals: "",
    });

    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByText("Writing mode is not available in this release.");
    expect(
      screen.queryByRole("heading", { name: "Choose your Writing companion" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Save setup/ })).toBeNull();
    expect(
      screen.queryByPlaceholderText("What do you do?"),
    ).not.toBeInTheDocument();
  });

  it("shows the play view (not SetupForm) for a Branching story with status=setup and persisted visible state", async () => {
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "branching",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue(branchingVisibleState());

    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByPlaceholderText("What do you do?");
    expect(
      screen.queryByRole("heading", { name: "Branching setup" }),
    ).not.toBeInTheDocument();
  });

  it("shows the RPG pre-play panel (not the configuration form) for an RPG story in setup", async () => {
    // ADR-015c: world first -- the GM conversation and its typed controls,
    // restored from the server's setup view on every load.
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue(null);
    mocks.getRpgSetup.mockResolvedValue(rpgSetupView());

    render(<StoryView storyId={baseStory.story_id} />);

    expect(await screen.findByTestId("rpg-setup-phase")).toHaveTextContent(
      "world",
    );
    expect(screen.getByPlaceholderText("What do you do?")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save setup" })).toBeNull();
  });

  it("re-reads the RPG setup view after each answered turn, even at the 50-turn transcript cap", async () => {
    // Codex whole-candidate review R1: the capped transcript length stops
    // changing at 50, so it cannot be what triggers the setup refresh.
    const capped = Array.from({ length: 50 }, (_, i) => ({
      turn_id: `t${i}`,
      user_input: `say ${i}`,
      assistant_output: `reply ${i}`,
      timestamp: "2026-01-01T00:00:00Z",
      intent_classification: "setup_confirmation" as const,
      schema_version: 1 as const,
    }));
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue(null);
    mocks.getLatestTranscript.mockResolvedValue(capped);
    mocks.getRpgSetup.mockResolvedValue(rpgSetupView());
    mocks.submitTurn.mockResolvedValue(deliveredResponse());

    render(<StoryView storyId={baseStory.story_id} />);
    await screen.findByTestId("rpg-setup-phase");
    const before = mocks.getRpgSetup.mock.calls.length;

    for (const text of ["first", "second"]) {
      fireEvent.change(screen.getByPlaceholderText("What do you do?"), {
        target: { value: text },
      });
      fireEvent.click(screen.getByRole("button", { name: /submit/i }));
      await waitFor(() =>
        expect(mocks.submitTurn).toHaveBeenCalledWith(baseStory.story_id, text),
      );
    }
    await waitFor(() =>
      expect(mocks.getRpgSetup.mock.calls.length).toBeGreaterThanOrEqual(
        before + 2,
      ),
    );
  });

  it("shows the play view immediately after saving Branching structured setup, before any confirmation turn", async () => {
    // Saved setup does not change story.status server-side (ADR-016
    // Decision 3 -- confirmation is an ordinary turn), so getVisibleState
    // still resolves null until onComplete's refresh() re-fetches it. The
    // immediate handoff must rely on the in-memory structuredSetupSaved
    // flag for this instant, not the persisted-visible-state signal alone.
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "branching",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue(null);

    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Branching setup" });
    mocks.getVisibleState.mockResolvedValue(branchingVisibleState());
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));

    await screen.findByPlaceholderText("What do you do?");
  });
});

// ADR-015c: StoryView now routes RPG setup to the pre-play panel; the
// retained configuration form (and its hydration guards) is exercised
// directly.
describe("RpgSetupForm reload preservation (PR #126 round 5)", () => {
  beforeEach(() => {
    localStorage.clear();
    // Round 12 additions to this suite assert on submitSetup call counts,
    // which the file's shared vi.hoisted mocks don't reset between tests.
    vi.clearAllMocks();
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
  });

  it("hydrates RpgSetupForm from persisted setup state instead of resetting to defaults", async () => {
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    mocks.getSetupState.mockResolvedValue({
      mode: "rpg",
      dice_handling: "player_rolls",
      gm_cheating: null,
      tone: "gritty",
      session_type: null,
      genre_flavor: null,
      house_rules: null,
      acceptable_content: null,
    });

    render(
      <SetupForm
        story={{ ...baseStory, mode: "rpg", status: "setup" }}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByRole("heading", { name: "RPG setup" });
    await waitFor(() =>
      expect(screen.getByLabelText("Dice handling")).toHaveValue(
        "player_rolls",
      ),
    );
    expect(screen.getByLabelText("Tone")).toHaveValue("gritty");
  });

  it("does not force the ai_rolls/balanced defaults back onto save when reopening a partially-configured story", async () => {
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    mocks.getSetupState.mockResolvedValue({
      mode: "rpg",
      dice_handling: "player_rolls",
      gm_cheating: null,
      tone: "gritty",
      session_type: null,
      genre_flavor: null,
      house_rules: null,
      acceptable_content: null,
    });
    mocks.submitSetup.mockResolvedValue({});

    render(
      <SetupForm
        story={{ ...baseStory, mode: "rpg", status: "setup" }}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByRole("heading", { name: "RPG setup" });
    await waitFor(() =>
      expect(screen.getByLabelText("Dice handling")).toHaveValue(
        "player_rolls",
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => expect(mocks.submitSetup).toHaveBeenCalled());
    expect(mocks.submitSetup).toHaveBeenCalledWith(
      baseStory.story_id,
      expect.objectContaining({
        dice_handling: "player_rolls",
        tone: "gritty",
      }),
    );
  });

  it("Round 12 remediation: disables Save while setup-state hydration is still in flight", async () => {
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    // Never resolves within this test -- simulates hydration still pending.
    mocks.getSetupState.mockReturnValue(new Promise(() => {}));

    render(
      <SetupForm
        story={{ ...baseStory, mode: "rpg", status: "setup" }}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByRole("heading", { name: "RPG setup" });
    expect(screen.getByRole("button", { name: "Save setup" })).toBeDisabled();
  });

  it("Round 12 remediation regression: a quick save after reload cannot submit ai_rolls/balanced before hydration completes", async () => {
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    let resolveHydration: (state: unknown) => void = () => {};
    mocks.getSetupState.mockReturnValue(
      new Promise((resolve) => {
        resolveHydration = resolve;
      }),
    );
    mocks.submitSetup.mockResolvedValue({});

    render(
      <SetupForm
        story={{ ...baseStory, mode: "rpg", status: "setup" }}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByRole("heading", { name: "RPG setup" });
    // Clicking a disabled submit button must not submit the form.
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));
    expect(mocks.submitSetup).not.toHaveBeenCalled();

    resolveHydration({
      mode: "rpg",
      dice_handling: "player_rolls",
      gm_cheating: null,
      tone: "gritty",
      session_type: null,
      genre_flavor: null,
      house_rules: null,
      acceptable_content: null,
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Save setup" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => expect(mocks.submitSetup).toHaveBeenCalled());
    expect(mocks.submitSetup).toHaveBeenCalledWith(
      baseStory.story_id,
      expect.objectContaining({
        dice_handling: "player_rolls",
        tone: "gritty",
      }),
    );
  });

  it("Round 12 remediation: hydration failure keeps Save disabled and shows a visible, retryable error", async () => {
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    mocks.getSetupState.mockRejectedValueOnce(new Error("network down"));

    render(
      <SetupForm
        story={{ ...baseStory, mode: "rpg", status: "setup" }}
        onComplete={vi.fn()}
      />,
    );

    await screen.findByRole("heading", { name: "RPG setup" });
    await screen.findByText(/Could not load saved RPG setup/i);
    expect(screen.getByRole("button", { name: "Save setup" })).toBeDisabled();

    mocks.getSetupState.mockResolvedValueOnce({
      mode: "rpg",
      dice_handling: "player_rolls",
      gm_cheating: null,
      tone: "gritty",
      session_type: null,
      genre_flavor: null,
      house_rules: null,
      acceptable_content: null,
    });
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Save setup" })).toBeEnabled(),
    );
    expect(
      screen.queryByText(/Could not load saved RPG setup/i),
    ).not.toBeInTheDocument();
  });
});

describe("StoryView Branching setup (ADR-016b: all styles, Begin story)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
    mocks.getSetupState.mockResolvedValue(null);
    mocks.submitSetup.mockResolvedValue({});
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "branching",
      status: "setup",
    });
  });

  it("offers every interaction style and a style-specific branch range", async () => {
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Branching setup" });
    const select = screen.getByLabelText("Interaction style");
    expect(select).toHaveValue("freeform_only");
    for (const name of [/hybrid/i, /true cyoa/i]) {
      const option = screen.getByRole("option", { name }) as HTMLOptionElement;
      expect(option.disabled).toBe(false);
    }
    expect(screen.queryByLabelText("Branch options per beat")).toBeNull();

    fireEvent.change(select, { target: { value: "true_cyoa" } });
    const range = screen.getByLabelText("Branch options per beat");
    expect(
      Array.from((range as HTMLSelectElement).options).map((o) => o.value),
    ).toEqual(["2-3", "2-4", "2-5"]);
    fireEvent.change(range, { target: { value: "2-5" } });
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));
    await waitFor(() =>
      expect(mocks.submitSetup).toHaveBeenCalledWith(
        baseStory.story_id,
        expect.objectContaining({
          interaction_style: "true_cyoa",
          branch_count_range: "2-5",
        }),
      ),
    );
  });

  it("shows Begin story for a saved setup and starts play only when clicked", async () => {
    const ready = { ...branchingVisibleState(), play_status: "setup" as const };
    const started = {
      ...branchingVisibleState(),
      play_status: "in_play" as const,
      last_branch_options: [
        { option_id: "opt_1", action_text: "Cross the bridge" },
        { option_id: "opt_2", action_text: "Wait for dawn" },
      ],
    };
    mocks.getVisibleState.mockResolvedValue(ready);
    mocks.beginStory.mockResolvedValue({
      outcome: "started",
      turn: { ...deliveredResponse(), visible_state: started },
      visible_state: started,
      schema_version: 1,
    });
    render(<StoryView storyId={baseStory.story_id} />);

    const begin = await screen.findByRole("button", { name: "Begin story" });
    expect(mocks.beginStory).not.toHaveBeenCalled();
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "branching",
      status: "in_play",
    });
    mocks.getVisibleState.mockResolvedValue(started);
    fireEvent.click(begin);

    await waitFor(() =>
      expect(mocks.beginStory).toHaveBeenCalledWith(baseStory.story_id),
    );
    expect(
      await screen.findByRole("button", { name: "Cross the bridge" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Begin story" })).toBeNull();
  });

  it("reopens a partially saved card-style setup, hydrated, instead of a Begin it cannot pass", async () => {
    // ADR-016b allows a partial save: Hybrid with no range yet.
    mocks.getVisibleState.mockResolvedValue({
      ...branchingVisibleState(),
      branch_count_range: null,
      play_status: "setup",
    });
    mocks.getSetupState.mockResolvedValue({
      mode: "branching",
      interaction_style: "hybrid",
      branching_cadence: "immersive",
      branch_count_range: null,
      length_preference: null,
      schema_version: 1,
    });
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Branching setup" });
    expect(screen.queryByRole("button", { name: "Begin story" })).toBeNull();
    await waitFor(() =>
      expect(screen.getByLabelText("Interaction style")).toHaveValue("hybrid"),
    );
    expect(screen.getByLabelText("Cadence")).toHaveValue("immersive");
    fireEvent.change(screen.getByLabelText("Branch options per beat"), {
      target: { value: "1-2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));
    await waitFor(() =>
      expect(mocks.submitSetup).toHaveBeenCalledWith(
        baseStory.story_id,
        expect.objectContaining({
          interaction_style: "hybrid",
          branching_cadence: "immersive",
          branch_count_range: "1-2",
        }),
      ),
    );
  });

  it("returns to setup, with the server's reason, when Begin reports setup_required", async () => {
    mocks.getVisibleState.mockResolvedValue({
      ...branchingVisibleState(),
      play_status: "setup",
    });
    mocks.getSetupState.mockResolvedValue(null);
    mocks.beginStory.mockRejectedValueOnce(
      new ApiRequestError(409, {
        error_code: "setup_required",
        message: "Complete Branching setup before beginning the story.",
        detail: null,
        schema_version: 1,
      }),
    );
    render(<StoryView storyId={baseStory.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Begin story" }));
    await screen.findByRole("heading", { name: "Branching setup" });
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Complete Branching setup before beginning the story.",
    );

    // A successful Save closes the form and clears the obsolete refusal,
    // leaving a valid Begin control.
    mocks.submitSetup.mockResolvedValue({});
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Save setup" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));
    expect(
      await screen.findByRole("button", { name: "Begin story" }),
    ).toBeEnabled();
    expect(
      screen.queryByText(
        "Complete Branching setup before beginning the story.",
      ),
    ).toBeNull();
  });

  it("clears an earlier failed opening's banner when another tab already started", async () => {
    mocks.getVisibleState.mockResolvedValue({
      ...branchingVisibleState(),
      play_status: "setup",
    });
    mocks.beginStory
      .mockResolvedValueOnce({
        outcome: "not_started",
        turn: pipelineErrorResponse(),
        visible_state: { ...branchingVisibleState(), play_status: "setup" },
        schema_version: 1,
      })
      .mockResolvedValueOnce({
        outcome: "already_started",
        turn: null,
        visible_state: { ...branchingVisibleState(), play_status: "in_play" },
        schema_version: 1,
      });
    render(<StoryView storyId={baseStory.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Begin story" }));
    await screen.findByText(/Please try submitting again/);
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "branching",
      status: "in_play",
    });
    fireEvent.click(screen.getByRole("button", { name: "Begin story" }));
    await waitFor(() =>
      expect(screen.queryByText(/Please try submitting again/)).toBeNull(),
    );
  });

  it("keeps the story ready to begin after a failed opening", async () => {
    mocks.getVisibleState.mockResolvedValue({
      ...branchingVisibleState(),
      play_status: "setup",
    });
    mocks.beginStory.mockResolvedValue({
      outcome: "not_started",
      turn: pipelineErrorResponse(),
      visible_state: { ...branchingVisibleState(), play_status: "setup" },
      schema_version: 1,
    });
    render(<StoryView storyId={baseStory.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Begin story" }));
    await waitFor(() => expect(mocks.beginStory).toHaveBeenCalled());
    expect(
      await screen.findByRole("button", { name: "Begin story" }),
    ).toBeEnabled();
  });

  it("submits interaction_style: freeform_only when saved without changes", async () => {
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Branching setup" });
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));

    await waitFor(() => expect(mocks.submitSetup).toHaveBeenCalled());
    expect(mocks.submitSetup).toHaveBeenCalledWith(
      baseStory.story_id,
      expect.objectContaining({
        mode: "branching",
        interaction_style: "freeform_only",
      }),
    );
  });
});

describe("StoryView load-error retry (PR #126 round 3)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
  });

  it("clears the stale error screen and shows the story after a successful retry", async () => {
    mocks.getStory.mockRejectedValueOnce(new Error("network blip"));
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByText("network blip");

    mocks.getStory.mockResolvedValue(baseStory);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    await screen.findByPlaceholderText("What do you do?");
    expect(screen.queryByText("network blip")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /retry/i }),
    ).not.toBeInTheDocument();
  });
});

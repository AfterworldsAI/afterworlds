import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "./api/client";
import type {
  StoryDetail,
  TurnSubmissionResponse,
  VisibleState,
} from "./api/client";
import StoryView from "./StoryView";

const baseStory: StoryDetail = {
  story_id: "11111111-1111-1111-1111-111111111111",
  title: "Test Story",
  mode: "writing",
  status: "in_play",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  schema_version: 1,
};

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
    branch_count_range: null,
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
    fireEvent.click(screen.getByRole("button", { name: "Save setup" }));

    await screen.findByText("post-setup refresh failed");
  });
});

describe("StoryView WritingSetupForm persona load (PR #126 round 13 P2)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "writing",
      status: "setup",
    });
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
    mocks.getSetupState.mockResolvedValue(null);
  });

  it("shows a visible error and keeps Save disabled when the persona gallery fails to load", async () => {
    mocks.listPersonas.mockRejectedValue(new Error("network down"));
    render(<StoryView storyId={baseStory.story_id} />);

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
    render(<StoryView storyId={baseStory.story_id} />);

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
    render(<StoryView storyId={baseStory.story_id} />);

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

  it("still shows SetupForm for a Writing story whose persona is set but specific_goals is still blank (PR #126 round 5 follow-up)", async () => {
    // A pre-round-5 (or otherwise incomplete) row: persona_id is set --
    // visible state is non-null -- but specific_goals is still blank.
    // visibleState !== null alone must not be treated as "Writing setup
    // complete": that would silently reopen the play view for a story
    // whose turns stay forced to SETUP_CONFIRMATION/NON_CANON_SUPPORT
    // forever, the exact defect round 5 fixed, resurfacing via this bypass
    // instead of the original path.
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

    await screen.findByRole("heading", {
      name: "Choose your Writing companion",
    });
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

  it("still shows SetupForm for an RPG story with status=setup and null visible state", async () => {
    // RPG visible state stays null until a concrete character sheet exists
    // -- unlike Writing/Branching, RPG must not skip its own setup screen
    // just because visible state happens to be non-null-checkable here.
    mocks.getStory.mockResolvedValue({
      ...baseStory,
      mode: "rpg",
      status: "setup",
    });
    mocks.getVisibleState.mockResolvedValue(null);

    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "RPG setup" });
    expect(
      screen.queryByPlaceholderText("What do you do?"),
    ).not.toBeInTheDocument();
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

describe("StoryView RPG setup reload preservation (PR #126 round 5)", () => {
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

    render(<StoryView storyId={baseStory.story_id} />);

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

    render(<StoryView storyId={baseStory.story_id} />);

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

    render(<StoryView storyId={baseStory.story_id} />);

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

    render(<StoryView storyId={baseStory.story_id} />);

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

    render(<StoryView storyId={baseStory.story_id} />);

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

describe("StoryView Branching setup defaults to freeform_only (PR #126 round 8 P1)", () => {
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

  it("defaults the interaction style select to freeform_only and disables hybrid/true_cyoa", async () => {
    render(<StoryView storyId={baseStory.story_id} />);

    await screen.findByRole("heading", { name: "Branching setup" });
    const select = screen.getByLabelText("Interaction style");
    expect(select).toHaveValue("freeform_only");

    const hybridOption = screen.getByRole("option", {
      name: /hybrid/i,
    }) as HTMLOptionElement;
    const trueCyoaOption = screen.getByRole("option", {
      name: /true cyoa/i,
    }) as HTMLOptionElement;
    expect(hybridOption.disabled).toBe(true);
    expect(trueCyoaOption.disabled).toBe(true);
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

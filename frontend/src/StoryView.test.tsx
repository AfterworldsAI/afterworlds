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
  getTranscript: vi.fn(),
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
      getTranscript: mocks.getTranscript,
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
    mocks.getTranscript.mockResolvedValue([]);
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

describe("StoryView setup handoff survives reload (PR #126 round 3)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getTranscript.mockResolvedValue([]);
    mocks.submitSetup.mockResolvedValue({});
    mocks.getSetupState.mockResolvedValue(null);
    mocks.listPersonas.mockResolvedValue({ mentors: [], peers: [] });
  });

  it("shows the play view (not SetupForm) for a Writing story with persisted play_status=in_play visible state", async () => {
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

  it("still shows SetupForm for a Writing story whose persona is set but play_status has not promoted to in_play (PR #126 round 5 follow-up)", async () => {
    // A pre-round-5 (or otherwise incomplete) row: persona_id is set --
    // visible state is non-null -- but specific_goals is still blank, so
    // play_status never promoted past SETUP. visibleState !== null alone
    // must not be treated as "Writing setup complete": that would silently
    // reopen the play view for a story whose turns stay forced to
    // SETUP_CONFIRMATION/NON_CANON_SUPPORT forever, the exact defect round
    // 5 fixed, resurfacing via this bypass instead of the original path.
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
    mocks.getTranscript.mockResolvedValue([]);
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
});

describe("StoryView Branching setup defaults to freeform_only (PR #126 round 8 P1)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getTranscript.mockResolvedValue([]);
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
    mocks.getTranscript.mockResolvedValue([]);
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

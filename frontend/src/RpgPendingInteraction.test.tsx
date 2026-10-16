import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "./api/client";
import type {
  PendingInteraction,
  StoryDetail,
  TurnSubmissionResponse,
} from "./api/client";
import StoryView from "./StoryView";

// CRD Issue 15b Phase 3: the minimum client lifecycle (15b-31, 15b-32, AC27)
// through the real play view, against a mocked API client.

const story: StoryDetail = {
  story_id: "11111111-1111-1111-1111-111111111111",
  title: "RPG",
  mode: "rpg",
  status: "in_play",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  schema_version: 1,
};
const SEQUENCE = "33333333-3333-3333-3333-333333333333";
const REQUEST = "44444444-4444-4444-4444-444444444444";
const TERM = "55555555-5555-5555-5555-555555555555";
const DECISION = "66666666-6666-6666-6666-666666666666";

function pendingRoll(revision = 1): PendingInteraction {
  return {
    schema_version: 1,
    sequence_id: SEQUENCE,
    interaction_phase: "pending_roll",
    pending_decision: null,
    pending_roll: {
      schema_version: 1,
      pending_roll_request_id: REQUEST,
      sequence_id: SEQUENCE,
      instruction_id: "77777777-7777-7777-7777-777777777777",
      instruction_revision: revision,
      purpose: "attack",
      interaction_phase: "pending_roll",
      progress: { schema_version: 1, step_index: 1 },
      display_label: "Dagger attack",
      display_expression: "1d20 + 1",
      terms: [
        {
          schema_version: 1,
          term_id: TERM,
          count: 1,
          sides: 20,
          selection_rule: "sum_all",
          contribution: "add",
        },
      ],
      visible_modifiers: [],
      visible_modifier_total: 1,
      adjustment_options: [
        {
          schema_version: 1,
          option_id: "finesse_dexterity",
          player_visible_label: "Use Dexterity",
        },
      ],
    },
  };
}

function pendingDecision(): PendingInteraction {
  return {
    schema_version: 1,
    sequence_id: SEQUENCE,
    interaction_phase: "pending_mechanical_decision",
    pending_roll: null,
    pending_decision: {
      schema_version: 1,
      decision_request_id: DECISION,
      sequence_id: SEQUENCE,
      decision_revision: 1,
      interaction_phase: "pending_mechanical_decision",
      prompt: "Knock the wolf out?",
      options: [
        {
          schema_version: 1,
          option_id: "knock_out",
          player_visible_label: "Knock it out",
        },
      ],
    },
  };
}

function ready(): PendingInteraction {
  return {
    schema_version: 1,
    sequence_id: SEQUENCE,
    interaction_phase: "ready_for_narration",
    pending_roll: null,
    pending_decision: null,
  };
}

function turn(
  disposition: TurnSubmissionResponse["disposition"],
): TurnSubmissionResponse {
  return {
    disposition,
    turn_id: disposition === "delivered" ? "t-1" : null,
    delivered_output: disposition === "delivered" ? "The wolf falls." : null,
    stable_prefix_cache_warmed: false,
    interaction_rejection_reason: null,
    interaction_rejection_message: null,
    pipeline_error_summary: disposition === "pipeline_error" ? "boom" : null,
    provider_refusal: null,
    pending_roll_redirect_message: null,
    settlement_warning: null,
    visible_state: null,
    schema_version: 1,
  };
}

const narratedTurn = {
  turn_id: "t-1",
  user_input: "I stab the wolf.",
  assistant_output: "The wolf falls.",
  timestamp: "2026-01-01T00:00:00Z",
  intent_classification: "in_character_action" as const,
  schema_version: 1 as const,
};

const mocks = vi.hoisted(() => ({
  getStory: vi.fn(),
  getLatestTranscript: vi.fn(),
  getVisibleState: vi.fn(),
  getPendingInteraction: vi.fn(),
  submitRoll: vi.fn(),
  applyAdjustment: vi.fn(),
  submitDecision: vi.fn(),
  resumeSequence: vi.fn(),
  submitTurn: vi.fn(),
}));

vi.mock("./api/client", async () => {
  const actual =
    await vi.importActual<typeof import("./api/client")>("./api/client");
  return { ...actual, api: mocks };
});

describe("StoryView RPG pending interaction (CRD Issue 15b)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
    mocks.getStory.mockResolvedValue(story);
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
  });

  it("submits the rolled faces and narrates at once when the action becomes ready", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(pendingRoll()) // load
      .mockResolvedValueOnce(null); // after the narration
    mocks.getLatestTranscript
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([narratedTurn]);
    mocks.submitRoll.mockResolvedValue(ready());
    mocks.resumeSequence.mockResolvedValue(turn("delivered"));
    render(<StoryView storyId={story.story_id} />);

    await screen.findByText("Roll needed: Dagger attack (1d20 + 1)");
    fireEvent.change(screen.getByLabelText(/faces rolled/), {
      target: { value: "15" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Submit physical roll" }),
    );

    await screen.findByText("The wolf falls.");
    expect(mocks.submitRoll).toHaveBeenCalledWith(story.story_id, {
      source: "physical_self_report",
      pending_roll_request_id: REQUEST,
      expected_instruction_revision: 1,
      term_results: [{ term_id: TERM, values: [15], schema_version: 1 }],
      schema_version: 1,
    });
    expect(mocks.resumeSequence).toHaveBeenCalledTimes(1);
    expect(mocks.resumeSequence).toHaveBeenCalledWith(story.story_id, SEQUENCE);
    expect(screen.queryByText(/Roll needed/)).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("applies an offered adjustment and a decision option through the API", async () => {
    mocks.getPendingInteraction.mockResolvedValueOnce(pendingRoll());
    mocks.applyAdjustment.mockResolvedValue(pendingDecision());
    mocks.submitDecision.mockResolvedValue(pendingRoll(2));
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Use Dexterity" }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Knock it out" }),
    );

    await waitFor(() => expect(mocks.submitDecision).toHaveBeenCalled());
    expect(mocks.applyAdjustment).toHaveBeenCalledWith(story.story_id, {
      pending_roll_request_id: REQUEST,
      expected_instruction_revision: 1,
      option_id: "finesse_dexterity",
      schema_version: 1,
    });
    expect(mocks.submitDecision).toHaveBeenCalledWith(story.story_id, {
      decision_request_id: DECISION,
      expected_decision_revision: 1,
      option_id: "knock_out",
      schema_version: 1,
    });
    expect(mocks.resumeSequence).not.toHaveBeenCalled();
  });

  it("offers the same resume affordance after a reload, without resuming by itself", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(ready())
      .mockResolvedValueOnce(null);
    mocks.resumeSequence.mockResolvedValue(turn("delivered"));
    render(<StoryView storyId={story.story_id} />);

    const resume = await screen.findByRole("button", {
      name: "Narrate the resolved action",
    });
    expect(mocks.resumeSequence).not.toHaveBeenCalled();
    fireEvent.click(resume);
    await waitFor(() => expect(mocks.resumeSequence).toHaveBeenCalledTimes(1));
  });

  it("reports a settled resume so the account view re-reads (CRD Issue 20)", async () => {
    const onTurnSettled = vi.fn();
    mocks.getPendingInteraction
      .mockResolvedValueOnce(ready())
      .mockResolvedValueOnce(null);
    mocks.resumeSequence.mockResolvedValue(turn("delivered"));
    render(
      <StoryView storyId={story.story_id} onTurnSettled={onTurnSettled} />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Narrate the resolved action",
      }),
    );
    await waitFor(() => expect(onTurnSettled).toHaveBeenCalledTimes(1));
  });

  it("treats an already-completed resume as success: refetch, no error", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(ready())
      .mockResolvedValueOnce(null);
    mocks.getLatestTranscript
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([narratedTurn]);
    mocks.resumeSequence.mockRejectedValue(
      new ApiRequestError(409, {
        error_code: "action_sequence_already_completed",
        message: "This action was already narrated.",
        detail: null,
        schema_version: 1,
      }),
    );
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Narrate the resolved action",
      }),
    );
    await screen.findByText("The wolf falls.");
    expect(mocks.getPendingInteraction).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Narrate the resolved action" }),
    ).not.toBeInTheDocument();
  });

  it("keeps a failed narration's ready affordance for a deliberate retry, never looping", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(pendingRoll())
      .mockResolvedValue(ready());
    mocks.submitRoll.mockResolvedValue(ready());
    mocks.resumeSequence.mockResolvedValue(turn("pipeline_error"));
    render(<StoryView storyId={story.story_id} />);

    fireEvent.change(await screen.findByLabelText(/faces rolled/), {
      target: { value: "15" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Submit physical roll" }),
    );

    await screen.findByText("boom", { exact: false });
    await screen.findByRole("button", { name: "Narrate the resolved action" });
    expect(mocks.resumeSequence).toHaveBeenCalledTimes(1);
  });

  it("shows a refused operation inline, rehydrates, and keeps the draft and turn input available", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(pendingRoll(1))
      .mockResolvedValueOnce(pendingRoll(2));
    mocks.submitRoll.mockRejectedValue(
      new ApiRequestError(409, {
        error_code: "pending_roll_revision_mismatch",
        message:
          "The roll instruction has changed. Refetch the pending interaction.",
        detail: null,
        schema_version: 1,
      }),
    );
    mocks.submitTurn.mockResolvedValue(turn("ooc_handled"));
    render(<StoryView storyId={story.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "(OOC) what now?" } });
    fireEvent.change(screen.getByLabelText(/faces rolled/), {
      target: { value: "15" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Submit physical roll" }),
    );

    await screen.findByText(/The roll instruction has changed/);
    await waitFor(() =>
      expect(mocks.getPendingInteraction).toHaveBeenCalledTimes(2),
    );
    expect(textarea).toHaveValue("(OOC) what now?");
    expect(textarea).not.toBeDisabled();
    // Out-of-character input stays available while the action is unresolved.
    fireEvent.click(screen.getByRole("button", { name: /^submit$/i }));
    await waitFor(() =>
      expect(mocks.submitTurn).toHaveBeenCalledWith(
        story.story_id,
        "(OOC) what now?",
      ),
    );
  });

  it("clears a failed narration's banner when the retry finds the action already narrated", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(ready()) // load
      .mockResolvedValueOnce(ready()) // after the failed narration
      .mockResolvedValueOnce(null); // after the success-equivalent replay
    mocks.resumeSequence
      .mockResolvedValueOnce(turn("pipeline_error"))
      .mockRejectedValueOnce(
        new ApiRequestError(409, {
          error_code: "action_sequence_already_completed",
          message: "This action was already narrated.",
          detail: null,
          schema_version: 1,
        }),
      );
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Narrate the resolved action",
      }),
    );
    await screen.findByText("boom", { exact: false });
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Narrate the resolved action",
      }),
    );
    await waitFor(() =>
      expect(mocks.getPendingInteraction).toHaveBeenCalledTimes(3),
    );
    await waitFor(() =>
      expect(screen.queryByRole("alert")).not.toBeInTheDocument(),
    );
  });

  it("never reads a pending interaction for a non-RPG story", async () => {
    mocks.getStory.mockResolvedValue({ ...story, mode: "writing" });
    render(<StoryView storyId={story.story_id} />);
    await screen.findByPlaceholderText("What do you do?");
    expect(mocks.getPendingInteraction).not.toHaveBeenCalled();
  });
});

// CRD Issue 19b: digital dice, scorecard, physical entry and recovery.

const ADV = "88888888-8888-8888-8888-888888888881";
const POOL = "88888888-8888-8888-8888-888888888882";
const PENALTY = "88888888-8888-8888-8888-888888888883";

/** A mixed instruction: 2d20 keep highest, 2d6, minus 1d4, two modifiers. */
function mixedRoll(revision = 1): PendingInteraction {
  const base = pendingRoll(revision);
  return {
    ...base,
    pending_roll: {
      ...base.pending_roll!,
      progress: { schema_version: 1, step_index: 2, known_step_count: null },
      display_label: "Heavy swing",
      display_expression: "2d20kh1 + 2d6 - 1d4 + 1",
      terms: [
        {
          schema_version: 1,
          term_id: ADV,
          count: 2,
          sides: 20,
          selection_rule: "keep_highest",
          keep_count: 1,
          contribution: "add",
          label: "Attack",
        },
        {
          schema_version: 1,
          term_id: POOL,
          count: 2,
          sides: 6,
          selection_rule: "sum_all",
          contribution: "add",
        },
        {
          schema_version: 1,
          term_id: PENALTY,
          count: 1,
          sides: 4,
          selection_rule: "sum_all",
          contribution: "subtract",
        },
      ],
      visible_modifiers: [
        {
          schema_version: 1,
          modifier_id: "99999999-9999-9999-9999-999999999991",
          label: "Proficiency",
          value: 2,
        },
        {
          schema_version: 1,
          modifier_id: "99999999-9999-9999-9999-999999999992",
          label: "Strength",
          value: -1,
        },
      ],
      visible_modifier_total: 1,
    },
  };
}

/** Browser randomness that lands on these faces (word = face - 1). */
function browserDice(...faces: number[]) {
  const words = faces.map((face) => face - 1);
  return vi
    .spyOn(globalThis.crypto, "getRandomValues")
    .mockImplementation(<T extends ArrayBufferView | null>(array: T): T => {
      (array as unknown as Uint32Array)[0] = words.shift()!;
      return array;
    });
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

const revisionMismatch = new ApiRequestError(409, {
  error_code: "pending_roll_revision_mismatch",
  message: "The roll instruction has changed. Refetch the pending interaction.",
  detail: null,
  schema_version: 1,
});

describe("StoryView inline dice (CRD Issue 19b)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
    mocks.getStory.mockResolvedValue(story);
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("rolls the live structured terms, previews them, and submits every raw face as inline_ui", async () => {
    mocks.getPendingInteraction.mockResolvedValue(mixedRoll());
    mocks.submitRoll.mockResolvedValue(pendingDecision());
    const random = browserDice(4, 17, 3, 5, 2);
    render(<StoryView storyId={story.story_id} />);

    await screen.findByText(
      "Roll needed: Heavy swing (2d20kh1 + 2d6 - 1d4 + 1)",
    );
    // Unknown step counts stay unknown; only public modifiers are listed.
    expect(screen.getByText("Step 2")).toBeInTheDocument();
    expect(screen.getByText("Proficiency + 2")).toBeInTheDocument();
    expect(screen.getByText("Strength - 1")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Roll preview" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Roll dice" }));
    const preview = screen.getByRole("group", { name: "Roll preview" });
    expect(
      within(preview).getByText(/Unsubmitted preview/),
    ).toBeInTheDocument();
    expect(within(preview).getByLabelText("4 discarded")).toBeInTheDocument();
    expect(within(preview).getByLabelText("17")).toBeInTheDocument();
    expect(within(preview).getByText(/subtotal \+ 17/)).toBeInTheDocument();
    expect(within(preview).getByText(/subtotal \+ 8/)).toBeInTheDocument();
    expect(within(preview).getByText(/subtotal - 2/)).toBeInTheDocument();
    // 17 + 8 - 2, and the visible modifier total once: + 1.
    expect(within(preview).getByText("Preview total: 24")).toBeInTheDocument();
    // One candidate per revision: no second roll is offered.
    expect(screen.queryByRole("button", { name: "Roll dice" })).toBeNull();
    expect(random).toHaveBeenCalledTimes(5);

    fireEvent.click(
      screen.getByRole("button", { name: "Submit digital roll" }),
    );
    await screen.findByText("Knock the wolf out?");
    expect(mocks.submitRoll).toHaveBeenCalledTimes(1);
    expect(mocks.submitRoll).toHaveBeenCalledWith(story.story_id, {
      source: "inline_ui",
      pending_roll_request_id: REQUEST,
      expected_instruction_revision: 1,
      term_results: [
        { term_id: ADV, values: [4, 17], schema_version: 1 },
        { term_id: POOL, values: [3, 5], schema_version: 1 },
        { term_id: PENALTY, values: [2], schema_version: 1 },
      ],
      schema_version: 1,
    });
  });

  it("never replays or re-rolls after an uncertain failure, and a new revision discards the candidate", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(mixedRoll(1)) // load
      .mockResolvedValueOnce(mixedRoll(1)) // after the lost response
      .mockResolvedValueOnce(mixedRoll(2)); // after the stale refusal
    mocks.submitRoll
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockRejectedValueOnce(revisionMismatch);
    const random = browserDice(4, 17, 3, 5, 2);
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Roll dice" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Submit digital roll" }),
    );
    await screen.findByText("Failed to fetch");
    await waitFor(() =>
      expect(mocks.getPendingInteraction).toHaveBeenCalledTimes(2),
    );
    // Same request and revision: the same candidate, offered only for a
    // deliberate resubmission.
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Submit digital roll" }),
      ).toBeEnabled(),
    );
    expect(screen.getByText("Preview total: 24")).toBeInTheDocument();
    expect(mocks.submitRoll).toHaveBeenCalledTimes(1);
    expect(random).toHaveBeenCalledTimes(5);

    fireEvent.click(
      screen.getByRole("button", { name: "Submit digital roll" }),
    );
    await screen.findByText(/The roll instruction has changed/);
    await waitFor(() =>
      expect(screen.queryByRole("group", { name: "Roll preview" })).toBeNull(),
    );
    expect(
      await screen.findByRole("button", { name: "Roll dice" }),
    ).toBeEnabled();
    expect(mocks.submitRoll).toHaveBeenCalledTimes(2);
    expect(mocks.submitRoll.mock.calls[1]![1]).toMatchObject({
      expected_instruction_revision: 1,
      term_results: [
        { term_id: ADV, values: [4, 17] },
        { term_id: POOL, values: [3, 5] },
        { term_id: PENALTY, values: [2] },
      ],
    });
    expect(random).toHaveBeenCalledTimes(5);
  });

  it("keeps every control disabled until a re-read succeeds", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(pendingRoll())
      .mockRejectedValueOnce(new TypeError("Failed to fetch pending"))
      .mockResolvedValueOnce(pendingRoll());
    mocks.submitRoll.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<StoryView storyId={story.story_id} />);

    fireEvent.change(await screen.findByLabelText(/faces rolled/), {
      target: { value: "15" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Submit physical roll" }),
    );
    await screen.findByText(/Failed to fetch pending/);
    for (const name of ["Roll dice", "Submit physical roll", "Use Dexterity"]) {
      expect(screen.getByRole("button", { name })).toBeDisabled();
    }
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Use Dexterity" }),
      ).toBeEnabled(),
    );
    expect(mocks.submitRoll).toHaveBeenCalledTimes(1);
  });

  it("starts one operation for a double click", async () => {
    mocks.getPendingInteraction.mockResolvedValue(pendingRoll());
    const roll = deferred<PendingInteraction>();
    mocks.submitRoll.mockReturnValue(roll.promise);
    browserDice(12);
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Roll dice" }));
    const submit = screen.getByRole("button", { name: "Submit digital roll" });
    act(() => {
      submit.click();
      submit.click(); // same tick: this render still shows it enabled
    });
    await act(async () => roll.resolve(pendingDecision()));
    expect(mocks.submitRoll).toHaveBeenCalledTimes(1);
  });

  it("offers no insecure fallback when browser randomness is missing; physical entry remains", async () => {
    mocks.getPendingInteraction.mockResolvedValue(pendingRoll());
    mocks.submitRoll.mockResolvedValue(pendingDecision());
    vi.stubGlobal("crypto", undefined);
    const mathRandom = vi.spyOn(Math, "random");
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Roll dice" }));
    expect(
      screen.getByText(/Secure browser randomness is unavailable/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Roll dice" })).toBeDisabled();
    expect(screen.queryByRole("group", { name: "Roll preview" })).toBeNull();
    expect(mathRandom).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText(/faces rolled/), {
      target: { value: "15" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Submit physical roll" }),
    );
    await waitFor(() =>
      expect(mocks.submitRoll).toHaveBeenCalledWith(
        story.story_id,
        expect.objectContaining({
          source: "physical_self_report",
          term_results: [{ term_id: TERM, values: [15], schema_version: 1 }],
        }),
      ),
    );
  });

  it("refuses malformed physical faces inline, before any request", async () => {
    mocks.getPendingInteraction.mockResolvedValue(mixedRoll());
    mocks.submitRoll.mockResolvedValue(pendingDecision());
    render(<StoryView storyId={story.story_id} />);

    const attack = await screen.findByLabelText(/^Attack .* faces rolled/);
    const pool = screen.getByLabelText(/^2d6 faces rolled/);
    const penalty = screen.getByLabelText(/^minus 1d4 faces rolled/);
    const submit = screen.getByRole("button", { name: "Submit physical roll" });
    const cases: [HTMLElement, string, string][] = [
      [attack, "1.0 3", "Enter whole numbers only."],
      [attack, "0x3 2", "Enter whole numbers only."],
      [attack, "1e1, 2", "Enter whole numbers only."],
      [attack, "17", "Enter exactly 2 faces."],
      [attack, "17 21", "Each face must be from 1 to 20."],
      [pool, "3 0", "Each face must be from 1 to 6."],
    ];
    for (const [input, value, message] of cases) {
      fireEvent.change(input, { target: { value } });
      expect(input).toHaveAttribute("aria-invalid", "true");
      expect(screen.getByText(message)).toBeInTheDocument();
      expect(submit).toBeDisabled();
    }
    fireEvent.change(attack, { target: { value: "4, 17" } });
    fireEvent.change(pool, { target: { value: "3 5" } });
    fireEvent.change(penalty, { target: { value: "2" } });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);
    await waitFor(() => expect(mocks.submitRoll).toHaveBeenCalledTimes(1));
    expect(mocks.submitRoll.mock.calls[0]![1]).toMatchObject({
      source: "physical_self_report",
      term_results: [
        { term_id: ADV, values: [4, 17] },
        { term_id: POOL, values: [3, 5] },
        { term_id: PENALTY, values: [2] },
      ],
    });
  });

  it("never lets an older pending read overwrite a newer advancement", async () => {
    const revised = pendingRoll(2);
    revised.pending_roll!.display_expression = "1d20 + 4";
    const slowRead = deferred<PendingInteraction | null>();
    mocks.getPendingInteraction
      .mockResolvedValueOnce(pendingRoll(1)) // load
      .mockReturnValueOnce(slowRead.promise); // the turn's follow-up read
    mocks.submitTurn.mockResolvedValue(turn("ooc_handled"));
    mocks.applyAdjustment.mockResolvedValue(revised);
    render(<StoryView storyId={story.story_id} />);

    fireEvent.change(await screen.findByPlaceholderText("What do you do?"), {
      target: { value: "(OOC) how far is the wolf?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^submit$/i }));
    await waitFor(() =>
      expect(mocks.getPendingInteraction).toHaveBeenCalledTimes(2),
    );
    fireEvent.click(screen.getByRole("button", { name: "Use Dexterity" }));
    await screen.findByText("Roll needed: Dagger attack (1d20 + 4)");
    await act(async () => slowRead.resolve(pendingRoll(1)));
    expect(
      screen.getByText("Roll needed: Dagger attack (1d20 + 4)"),
    ).toBeInTheDocument();
  });

  it("takes the Sojourner to the unresolved roll when the backend holds an in-character action", async () => {
    mocks.getPendingInteraction.mockResolvedValue(pendingRoll());
    mocks.submitTurn.mockResolvedValue({
      ...turn("blocked_pending_roll"),
      pending_roll_redirect_message: "Roll needed: Dagger attack (1d20 + 1)",
    });
    render(<StoryView storyId={story.story_id} />);

    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "I run away." } });
    fireEvent.click(screen.getByRole("button", { name: /^submit$/i }));
    await waitFor(() =>
      expect(
        screen.getByRole("region", { name: "Pending action" }).parentElement,
      ).toHaveFocus(),
    );
    expect(textarea).toHaveValue("I run away.");
    expect(mocks.submitRoll).not.toHaveBeenCalled();
  });

  it("never resumes a story the Sojourner has left mid-operation", async () => {
    mocks.getPendingInteraction.mockResolvedValue(pendingRoll());
    const roll = deferred<PendingInteraction>();
    mocks.submitRoll.mockReturnValue(roll.promise);
    browserDice(12);
    const { unmount } = render(<StoryView storyId={story.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Roll dice" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Submit digital roll" }),
    );
    unmount();
    await act(async () => roll.resolve(ready()));
    expect(mocks.resumeSequence).not.toHaveBeenCalled();
  });
});

describe("StoryView inline dice refusals (CRD Issue 19b)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
    mocks.getStory.mockResolvedValue(story);
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it.each([
    [409, "turn_in_flight", "Another action for this story is in progress."],
    [404, "pending_roll_not_found", "That roll is no longer pending."],
    [422, "pending_roll_term_mismatch", "The submitted dice do not match."],
    [422, "pending_roll_invalid_value", "A die value is not possible."],
  ] as const)(
    "shows %i %s inline, re-reads before re-enabling, and never resubmits by itself",
    async (status, code, message) => {
      const reread = deferred<PendingInteraction | null>();
      mocks.getPendingInteraction
        .mockResolvedValueOnce(pendingRoll())
        .mockReturnValueOnce(reread.promise);
      mocks.submitRoll.mockRejectedValue(
        new ApiRequestError(status, {
          error_code: code,
          message,
          detail: null,
          schema_version: 1,
        }),
      );
      browserDice(9);
      render(<StoryView storyId={story.story_id} />);

      fireEvent.click(await screen.findByRole("button", { name: "Roll dice" }));
      fireEvent.click(
        screen.getByRole("button", { name: "Submit digital roll" }),
      );
      await screen.findByText(message);
      const submit = screen.getByRole("button", {
        name: "Submit digital roll",
      });
      expect(submit).toBeDisabled(); // until the re-read lands
      await act(async () => reread.resolve(pendingRoll()));
      await waitFor(() => expect(submit).toBeEnabled());
      expect(screen.getByLabelText("9")).toBeInTheDocument(); // same candidate
      expect(mocks.submitRoll).toHaveBeenCalledTimes(1);
    },
  );

  it("keeps the first candidate when Roll dice is clicked twice in one tick", async () => {
    mocks.getPendingInteraction.mockResolvedValue(pendingRoll());
    browserDice(5, 9);
    render(<StoryView storyId={story.story_id} />);

    const roll = await screen.findByRole("button", { name: "Roll dice" });
    act(() => {
      roll.click();
      roll.click();
    });
    expect(screen.getByLabelText("5")).toBeInTheDocument();
    expect(screen.queryByLabelText("9")).toBeNull();
  });

  it("offers no digital roll for terms the backend would never issue; physical entry remains", async () => {
    const repeated = pendingRoll();
    const term = repeated.pending_roll!.terms[0]!;
    repeated.pending_roll!.terms = [term, { ...term }]; // a repeated term id
    mocks.getPendingInteraction.mockResolvedValue(repeated);
    const random = browserDice(3, 4);
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(await screen.findByRole("button", { name: "Roll dice" }));
    expect(
      screen.getByText(/Digital dice are unavailable for this roll/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Roll preview" })).toBeNull();
    expect(random).not.toHaveBeenCalled();
    expect(screen.getAllByLabelText(/faces rolled/)).toHaveLength(2);
  });
});

describe("StoryView uncertain narration (CRD Issue 19b)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
    mocks.getStory.mockResolvedValue(story);
    mocks.getLatestTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const narrateButton = () =>
    screen.getByRole("button", { name: "Narrate the resolved action" });

  it("offers no resume after a lost resume and a failed re-read until a read succeeds", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(ready()) // load
      .mockRejectedValueOnce(new TypeError("Failed to fetch pending"))
      .mockResolvedValueOnce(ready()) // the explicit retry
      .mockResolvedValueOnce(null); // after the deliberate resume
    mocks.resumeSequence
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(turn("delivered"));
    render(<StoryView storyId={story.story_id} />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Narrate the resolved action",
      }),
    );
    await screen.findByText(/Failed to fetch pending/);
    expect(narrateButton()).toBeDisabled();
    expect(mocks.resumeSequence).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(narrateButton()).toBeEnabled());
    expect(mocks.resumeSequence).toHaveBeenCalledTimes(1); // never replayed

    fireEvent.click(narrateButton());
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: "Narrate the resolved action" }),
      ).toBeNull(),
    );
    expect(mocks.resumeSequence).toHaveBeenCalledTimes(2);
  });

  it("holds the ready affordance after an automatic resume is lost and its re-read fails", async () => {
    mocks.getPendingInteraction
      .mockResolvedValueOnce(pendingRoll()) // load
      .mockRejectedValueOnce(new TypeError("Failed to fetch pending"))
      .mockResolvedValueOnce(ready()); // the explicit retry
    mocks.submitRoll.mockResolvedValue(ready());
    mocks.resumeSequence.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<StoryView storyId={story.story_id} />);

    fireEvent.change(await screen.findByLabelText(/faces rolled/), {
      target: { value: "15" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Submit physical roll" }),
    );
    await screen.findByText(/Failed to fetch pending/);
    expect(narrateButton()).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(narrateButton()).toBeEnabled());
    expect(mocks.submitRoll).toHaveBeenCalledTimes(1);
    expect(mocks.resumeSequence).toHaveBeenCalledTimes(1);
  });
});

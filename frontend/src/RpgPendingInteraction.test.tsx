import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

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
    fireEvent.click(screen.getByRole("button", { name: "Submit roll" }));

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
    fireEvent.click(screen.getByRole("button", { name: "Submit roll" }));

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
    fireEvent.click(screen.getByRole("button", { name: "Submit roll" }));

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

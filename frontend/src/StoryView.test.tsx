import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "./api/client";
import type { StoryDetail, TurnSubmissionResponse } from "./api/client";
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
  submitTurn: vi.fn(),
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
      submitTurn: mocks.submitTurn,
    },
  };
});

describe("StoryView draft preservation (Binding Decision 6)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getStory.mockResolvedValue(baseStory);
    mocks.getTranscript.mockResolvedValue([]);
    mocks.getVisibleState.mockResolvedValue(null);
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

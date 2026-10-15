/**
 * The single frontend API-client module (Binding Decision 12) -- every
 * request flows through here. No component constructs its own fetch call
 * or base URL.
 */
import type { components, operations } from "./schema";

// Generated: FastAPI's OpenAPI export doesn't reflect
// `@app.exception_handler`-produced shapes on its own, so the CRD Issue 15b
// routes declare ApiError in their `responses=` (api/errors.py), which puts
// ApiError/ApiErrorCode into components["schemas"].
export type ApiErrorCode = components["schemas"]["ApiErrorCode"];
export type ApiError = components["schemas"]["ApiError"];

export type StoryListItem = components["schemas"]["StoryListItemDTO"];
export type StoryDetail = components["schemas"]["StoryDetailDTO"];
export type CreateStoryRequest = components["schemas"]["CreateStoryRequest"];
export type TurnSubmissionResponse =
  components["schemas"]["TurnSubmissionResponse"];
export type TranscriptTurn = components["schemas"]["TranscriptTurnDTO"];
export type VisibleState =
  | components["schemas"]["RpgVisibleState"]
  | components["schemas"]["BranchingVisibleState"]
  | components["schemas"]["WritingVisibleState"];
export type SetupRequest =
  operations["submit_setup_api_stories__story_id__setup_post"]["requestBody"]["content"]["application/json"];
export type SetupState = NonNullable<
  components["schemas"]["SetupStateResponse"]["setup_state"]
>;
export type PersonaGallery = components["schemas"]["PersonaGalleryResponse"];
// CRD Issue 15b: the RPG pending interaction and its deterministic operations.
export type PendingInteraction =
  components["schemas"]["ActionResolutionAdvanceResult"];
export type PendingRoll = components["schemas"]["PlayerRollInstructionView"];
export type PendingDecision =
  components["schemas"]["PendingMechanicalDecisionView"];
export type RollSubmission =
  | components["schemas"]["RawPlayerRollSubmission"]
  | components["schemas"]["PhysicalAggregateRollSubmission"];
export type RollAdjustmentRequest =
  components["schemas"]["RollAdjustmentRequest"];
export type DecisionSubmission =
  components["schemas"]["MechanicalDecisionSubmission"];

export class ApiRequestError extends Error {
  constructor(
    public status: number,
    public apiError: ApiError,
  ) {
    super(apiError.message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as ApiError | null;
    if (body && "error_code" in body) {
      throw new ApiRequestError(res.status, body);
    }
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<components["schemas"]["HealthResponse"]>("/api/health"),

  listStories: () =>
    request<components["schemas"]["StoryListResponse"]>("/api/stories").then(
      (r) => r.stories,
    ),

  createStory: (body: CreateStoryRequest) =>
    request<StoryDetail>("/api/stories", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getStory: (storyId: string) =>
    request<StoryDetail>(`/api/stories/${storyId}`),

  getTranscript: (storyId: string, limit = 50, offset = 0) =>
    request<components["schemas"]["TranscriptResponse"]>(
      `/api/stories/${storyId}/turns?limit=${limit}&offset=${offset}`,
    ).then((r) => r.turns),

  // Round 11 remediation (PR #126 P2): the play view must show the most
  // recently delivered turns, not always the first page -- a story past the
  // default page size otherwise never shows new output on refresh even
  // though it was correctly persisted.
  getLatestTranscript: (storyId: string, limit = 50) =>
    request<components["schemas"]["TranscriptResponse"]>(
      `/api/stories/${storyId}/turns?limit=${limit}&latest=true`,
    ).then((r) => r.turns),

  submitTurn: (storyId: string, userInput: string) =>
    request<TurnSubmissionResponse>(`/api/stories/${storyId}/turns`, {
      method: "POST",
      body: JSON.stringify({ user_input: userInput, schema_version: 1 }),
    }),

  getVisibleState: (storyId: string) =>
    request<components["schemas"]["VisibleStateResponse"]>(
      `/api/stories/${storyId}/visible-state`,
    ).then((r) => r.visible_state ?? null),

  submitSetup: (storyId: string, body: SetupRequest) =>
    request<components["schemas"]["SetupResponse"]>(
      `/api/stories/${storyId}/setup`,
      { method: "POST", body: JSON.stringify(body) },
    ),

  getSetupState: (storyId: string) =>
    request<components["schemas"]["SetupStateResponse"]>(
      `/api/stories/${storyId}/setup`,
    ).then((r) => r.setup_state ?? null),

  listPersonas: () => request<PersonaGallery>("/api/personas"),

  getPendingInteraction: (storyId: string) =>
    request<components["schemas"]["PendingInteractionResponse"]>(
      `/api/stories/${storyId}/rpg/pending-interaction`,
    ).then((r) => r.interaction ?? null),

  submitRoll: (storyId: string, body: RollSubmission) =>
    request<PendingInteraction>(`/api/stories/${storyId}/rpg/rolls`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  applyAdjustment: (storyId: string, body: RollAdjustmentRequest) =>
    request<PendingInteraction>(`/api/stories/${storyId}/rpg/adjustments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  submitDecision: (storyId: string, body: DecisionSubmission) =>
    request<PendingInteraction>(`/api/stories/${storyId}/rpg/decisions`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // A turn: the server selects the access path and settles as for any turn.
  // 409 action_sequence_already_completed is success-equivalent (15b-32).
  resumeSequence: (storyId: string, sequenceId: string) =>
    request<TurnSubmissionResponse>(
      `/api/stories/${storyId}/rpg/sequences/${sequenceId}/resume`,
      { method: "POST" },
    ),
};

/**
 * The single frontend API-client module (Binding Decision 12) -- every
 * request flows through here. No component constructs its own fetch call
 * or base URL.
 */
import type { components, operations } from "./schema";

// Hand-typed, not generated: FastAPI's OpenAPI export doesn't reflect
// `@app.exception_handler`-produced shapes, only response_model= schemas --
// so ApiError (from api/errors.py) never appears in components["schemas"].
// Keep this in sync with ApiError/ApiErrorCode by hand.
export type ApiErrorCode =
  | "not_found"
  | "validation_failed"
  | "entitlement_blocked"
  | "byok_credentials_required"
  | "turn_in_flight"
  | "setup_required"
  | "setup_state_conflict"
  | "internal_error";

export interface ApiError {
  error_code: ApiErrorCode;
  message: string;
  detail: Record<string, string> | null;
  schema_version: 1;
}

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
export type PersonaGallery = components["schemas"]["PersonaGalleryResponse"];

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

  submitTurn: (storyId: string, userInput: string) =>
    request<TurnSubmissionResponse>(`/api/stories/${storyId}/turns`, {
      method: "POST",
      body: JSON.stringify({ user_input: userInput }),
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

  listPersonas: () => request<PersonaGallery>("/api/personas"),
};

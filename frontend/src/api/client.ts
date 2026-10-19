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
export type BeginStoryResponse = components["schemas"]["BeginStoryResponse"];
// ADR-015c: RPG product startup.
export type RpgSetupView = components["schemas"]["RpgSetupViewDTO"];
export type RpgSetupConfiguration =
  components["schemas"]["RpgSetupConfigurationDTO"];
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

// CRD Issue 20: authoritative account view and BYOK settings.
export type AccountStatus = components["schemas"]["AccountStatusResponse"];
export type ByokProviderName = components["schemas"]["ByokProvider"];

// Prerequisite #205: remote session presentation state. Never authority --
// the server decides every request from its own session record.
export type SessionStatus = components["schemas"]["SessionStatusResponse"];

export class ApiRequestError extends Error {
  constructor(
    public status: number,
    public apiError: ApiError,
  ) {
    super(apiError.message);
  }
}

// Called when the server reports that the session is missing, expired or
// revoked, so the app can return to sign-in. One listener: the App.
let onSignedOut: (() => void) | null = null;
export function setSignedOutListener(listener: (() => void) | null): void {
  onSignedOut = listener;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    // The custom header marks a same-origin client request: the remote
    // server refuses state-changing requests without it (cross-site forms
    // cannot set it). Cookies are HttpOnly; the client never stores them.
    headers: {
      "Content-Type": "application/json",
      "X-Afterworlds-Request": "1",
      ...init?.headers,
    },
    credentials: "same-origin",
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as ApiError | null;
    if (body && "error_code" in body) {
      if (res.status === 401 && body.error_code === "authentication_required") {
        onSignedOut?.();
      }
      throw new ApiRequestError(res.status, body);
    }
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<components["schemas"]["HealthResponse"]>("/api/health"),

  // Prerequisite #205: remote identity. Codes arrive only by notice, never
  // in a response; every outcome of register/recovery reads the same.
  getSessionStatus: () => request<SessionStatus>("/api/auth/session"),

  signIn: (contactAddress: string, password: string) =>
    request<SessionStatus>("/api/auth/sign-in", {
      method: "POST",
      body: JSON.stringify({ contact_address: contactAddress, password }),
    }),

  signOut: () =>
    request<SessionStatus>("/api/auth/sign-out", { method: "POST" }),

  register: (contactAddress: string) =>
    request<components["schemas"]["AcceptedResponse"]>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ contact_address: contactAddress }),
    }),

  completeRegistration: (
    contactAddress: string,
    code: string,
    password: string,
  ) =>
    request<components["schemas"]["AcceptedResponse"]>(
      "/api/auth/register/complete",
      {
        method: "POST",
        body: JSON.stringify({
          contact_address: contactAddress,
          code,
          password,
        }),
      },
    ),

  beginRecovery: (contactAddress: string) =>
    request<components["schemas"]["AcceptedResponse"]>("/api/auth/recovery", {
      method: "POST",
      body: JSON.stringify({ contact_address: contactAddress }),
    }),

  completeRecovery: (
    contactAddress: string,
    code: string,
    newPassword: string,
  ) =>
    request<components["schemas"]["AcceptedResponse"]>(
      "/api/auth/recovery/complete",
      {
        method: "POST",
        body: JSON.stringify({
          contact_address: contactAddress,
          code,
          new_password: newPassword,
        }),
      },
    ),

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

  // ADR-016b: start a configured Branching story (its opening and first
  // cards). A repeat answers "already_started" without any provider call.
  beginStory: (storyId: string) =>
    request<BeginStoryResponse>(`/api/stories/${storyId}/begin`, {
      method: "POST",
    }),

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

  // ADR-015c: typed RPG setup operations. None calls a provider or settles.
  getRpgSetup: (storyId: string) =>
    request<RpgSetupView>(`/api/stories/${storyId}/rpg/setup`),

  confirmWorld: (storyId: string, expectedWorldRevision: number) =>
    request<RpgSetupView>(`/api/stories/${storyId}/rpg/setup/confirm-world`, {
      method: "POST",
      body: JSON.stringify({ expected_world_revision: expectedWorldRevision }),
    }),

  selectRulesPackage: (storyId: string, packageUuid: string) =>
    request<RpgSetupView>(`/api/stories/${storyId}/rpg/setup/rules-package`, {
      method: "POST",
      body: JSON.stringify({ package_uuid: packageUuid }),
    }),

  acceptCharacter: (storyId: string, expectedCandidateRevision: number) =>
    request<RpgSetupView>(
      `/api/stories/${storyId}/rpg/setup/accept-character`,
      {
        method: "POST",
        body: JSON.stringify({
          expected_candidate_revision: expectedCandidateRevision,
        }),
      },
    ),

  // Confirms exactly what the GM's summary presented, at its revision.
  completeRpgSetup: (storyId: string, expectedConfigurationRevision: number) =>
    request<RpgSetupView>(`/api/stories/${storyId}/rpg/setup/complete`, {
      method: "POST",
      body: JSON.stringify({
        expected_configuration_revision: expectedConfigurationRevision,
      }),
    }),

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

  // CRD Issue 20. Every settings operation returns the refreshed account
  // view. The raw key travels only in this request body -- never a URL,
  // never returned, never stored by the client.
  getAccount: () => request<AccountStatus>("/api/account"),

  saveCredential: (provider: ByokProviderName, apiKey: string) =>
    request<AccountStatus>(`/api/account/byok/${provider}/credential`, {
      method: "PUT",
      body: JSON.stringify({ api_key: apiKey }),
    }),

  removeCredential: (provider: ByokProviderName) =>
    request<AccountStatus>(`/api/account/byok/${provider}/credential`, {
      method: "DELETE",
    }),

  setProviderEnabled: (provider: ByokProviderName, enabled: boolean) =>
    request<AccountStatus>(`/api/account/byok/${provider}/enabled`, {
      method: "PUT",
      body: JSON.stringify({ enabled }),
    }),

  setOpenRouterModel: (modelIdentifier: string | null) =>
    request<AccountStatus>("/api/account/byok/openrouter/model", {
      method: "PUT",
      body: JSON.stringify({ model_identifier: modelIdentifier }),
    }),

  // The only operation here that contacts a provider.
  validateCredential: (provider: ByokProviderName) =>
    request<AccountStatus>(`/api/account/byok/${provider}/validate`, {
      method: "POST",
      body: JSON.stringify({ acknowledge_provider_contact: true }),
    }),
};

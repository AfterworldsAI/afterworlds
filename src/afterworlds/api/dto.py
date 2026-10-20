"""Backend-owned API view models — Binding Decision 9.

All DTOs: Pydantic, ``extra="forbid"``, ``schema_version: Literal[1]``, str
enums, no ORM rows. These are a deliberate, versioned contract distinct from
internal service/domain models.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr, StrictBool, StrictInt, field_validator

from afterworlds.api.errors import ApiErrorCode
from afterworlds.entitlement.enums import HostedUnavailableReason, RuntimeAccessPath
from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    CritiqueIntensity,
    DiceHandling,
    IntentType,
    InteractionRejectionReason,
    InteractionStyle,
    LengthPreference,
    RpgSessionType,
    RpgTone,
    StoryMode,
    StyleDensity,
    WritingForm,
)
from afterworlds.models.rpg import ActionResolutionAdvanceResult, RpgVisibleState
from afterworlds.pipeline.branching.models import BranchingVisibleState
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
from afterworlds.pipeline.provider.credentials import ValidationStatus
from afterworlds.pipeline.writing.models import WritingVisibleState


class StoryPlayStatus(StrEnum):
    """API-facing setup/play status, shared shape across all three modes."""

    SETUP = "setup"
    IN_PLAY = "in_play"


class HealthResponse(BaseModel):
    model_config = {"extra": "forbid"}

    status: Literal["ok"]
    db_reachable: bool
    schema_version: Literal[1] = 1


class StoryListItemDTO(BaseModel):
    model_config = {"extra": "forbid"}

    story_id: UUID
    title: str
    mode: StoryMode
    status: StoryPlayStatus
    updated_at: datetime
    schema_version: Literal[1] = 1


class StoryListResponse(BaseModel):
    model_config = {"extra": "forbid"}

    stories: list[StoryListItemDTO]
    schema_version: Literal[1] = 1


class StoryDetailDTO(BaseModel):
    model_config = {"extra": "forbid"}

    story_id: UUID
    title: str
    mode: StoryMode
    status: StoryPlayStatus
    created_at: datetime
    updated_at: datetime
    schema_version: Literal[1] = 1


class CreateStoryRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    mode: StoryMode
    # RPG only; ignored for other modes. No default per-mode business
    # meaning is inferred here -- this is presentation-form input only.
    character_name: str | None = None
    schema_version: Literal[1] = 1


class TurnSubmissionRequest(BaseModel):
    model_config = {"extra": "forbid"}

    user_input: str
    schema_version: Literal[1] = 1


class ProviderRefusalSummaryDTO(BaseModel):
    """Advisory only -- never authoritative policy (mirrors ProviderRefusal).

    Deliberately excludes ``raw_response_excerpt``, ``pass_identifier``, and
    ``refusal_category``: internal routing/audit detail, not a client
    contract (Binding Decision 9).
    """

    model_config = {"extra": "forbid"}

    provider: str
    coarse_reason: str | None = None
    schema_version: Literal[1] = 1


class TurnSubmissionResponse(BaseModel):
    """The turn-submission envelope (Binding Decisions 3, 6, 10, 11)."""

    model_config = {"extra": "forbid"}

    disposition: PipelineDisposition
    turn_id: UUID | None
    delivered_output: str | None = None
    stable_prefix_cache_warmed: bool = False
    interaction_rejection_reason: InteractionRejectionReason | None = None
    interaction_rejection_message: str | None = None
    pipeline_error_summary: str | None = None
    provider_refusal: ProviderRefusalSummaryDTO | None = None
    pending_roll_redirect_message: str | None = None
    settlement_warning: str | None = None
    # Refreshed visible-state for the story's mode: one fetch in the same
    # session/transaction as the turn, before commit -- avoids a client-side
    # read race after this turn's writes land. None whenever the owning mode
    # service has nothing to report yet (e.g. setup not started).
    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1


class RpgSetupRequest(BaseModel):
    """RPG play-config form fields. Conversational setup (character creation,
    world-building) goes through ordinary turn submission, not this route --
    Issue 15's own pipeline owns setup_phase/play_status progression."""

    model_config = {"extra": "forbid"}

    mode: Literal["rpg"]
    dice_handling: DiceHandling | None = None
    gm_cheating: bool | None = None
    tone: RpgTone | None = None
    session_type: RpgSessionType | None = None
    genre_flavor: str | None = None
    house_rules: str | None = None
    acceptable_content: str | None = None
    #: ADR-015c: required while the story is in RPG setup -- the configuration
    #: revision the edited form was based on; a stale one is a 409.
    expected_configuration_revision: StrictInt | None = None
    schema_version: Literal[1] = 1


class BranchingSetupRequest(BaseModel):
    """Branching structured setup fields. The confirmation pass itself is an
    ordinary DELIVERED turn (ADR-016 Decision 3) -- submit it via
    POST .../turns after this call, not through this route."""

    model_config = {"extra": "forbid"}

    mode: Literal["branching"]
    interaction_style: InteractionStyle | None = None
    branching_cadence: BranchingCadence | None = None
    branch_count_range: BranchCountRange | None = None
    length_preference: LengthPreference | None = None
    clear_branch_count_range: bool = False
    schema_version: Literal[1] = 1


class WritingSetupRequest(BaseModel):
    """Writing setup fields. ``persona_id`` is required -- no default persona.

    ``dialogue_narration_ratio`` and ``beat_constraints`` are validated here
    to match ``WritingSessionState``'s own validators (P2 remediation, PR
    #126 review round 4): ``apply_writing_config_update`` assumes its caller
    already validated these -- true for its one production caller
    (``WritingConfigUpdate``, the OOC extractor's DTO), but this route calls
    it directly with unvalidated client input. Without this, an out-of-range
    ratio or a blank beat constraint would flush to the row, then the
    immediately-following ``build_visible_state`` re-read would raise while
    reconstructing ``WritingSessionState``, turning a client validation
    problem into an internal 500 instead of a typed 422.
    """

    model_config = {"extra": "forbid"}

    mode: Literal["writing"]
    persona_id: str
    # Required and nonblank (PR #126 review round 5, owner decision): the
    # server can only legitimately promote play_status to IN_PLAY -- the
    # signal turns.py uses to derive server-owned Writing turn provenance --
    # once WritingSessionState's own IN_PLAY invariant (nonblank persona_id
    # AND nonblank specific_goals) is genuinely satisfied. specific_goals is
    # user-facing content (injected into the model prompt and rendered in
    # the visible-state sidebar), so it must come from the Sojourner, not a
    # server-synthesized placeholder.
    specific_goals: str
    critique_intensity: CritiqueIntensity | None = None
    form: WritingForm | None = None
    form_other: str | None = None
    tense: str | None = None
    pov: str | None = None
    style_density: StyleDensity | None = None
    dialogue_narration_ratio: Annotated[int, Field(ge=0, le=100)] | None = None
    genre_conventions: str | None = None
    acceptable_content: str | None = None
    beat_constraints: list[str] | None = None
    schema_version: Literal[1] = 1

    @field_validator("specific_goals")
    @classmethod
    def _specific_goals_nonblank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("specific_goals must not be blank")
        return v

    @field_validator("beat_constraints")
    @classmethod
    def _beat_constraints_nonblank(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for constraint in v:
                if not constraint.strip():
                    raise ValueError("beat_constraints must not contain empty strings")
        return v


SetupRequest = Annotated[
    RpgSetupRequest | BranchingSetupRequest | WritingSetupRequest,
    Field(discriminator="mode"),
]


class BeginStoryResponse(BaseModel):
    """``POST .../begin`` (ADR-016b). ``started``: the opening was delivered
    (``turn`` carries it). ``not_started``: the opening failed typed and the
    story stays ready to begin (``turn`` carries the disposition, never
    candidate prose). ``already_started``: a no-op -- no provider call, Turn
    or deduction -- with the current persisted visible state."""

    model_config = {"extra": "forbid"}

    outcome: Literal["started", "not_started", "already_started"]
    turn: TurnSubmissionResponse | None = None
    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1


class SetupResponse(BaseModel):
    model_config = {"extra": "forbid"}

    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1


class RpgSetupStateDTO(BaseModel):
    """Currently-persisted RPG setup/config fields (PR #126 review round 5,
    P2). Unlike ``RpgSetupRequest``, every field is optional -- this reflects
    whatever has been saved so far, which may be partial or (for a brand-new
    story) all-default. Read-only mirror of ``RpgSetupRequest``'s field set;
    not a general character-sheet or setup-progress surface.
    """

    model_config = {"extra": "forbid"}

    mode: Literal["rpg"]
    dice_handling: DiceHandling | None = None
    gm_cheating: bool | None = None
    tone: RpgTone | None = None
    session_type: RpgSessionType | None = None
    genre_flavor: str | None = None
    house_rules: str | None = None
    acceptable_content: str | None = None
    schema_version: Literal[1] = 1


class BranchingSetupStateDTO(BaseModel):
    """Currently-persisted Branching setup/config fields. Branching already
    bypasses SetupForm on reload once persisted visible state exists
    (StoryView's ``structuredSetupPersisted``), so no frontend hydration
    consumes this today -- included for GET .../setup symmetry across modes.
    """

    model_config = {"extra": "forbid"}

    mode: Literal["branching"]
    interaction_style: InteractionStyle | None = None
    branching_cadence: BranchingCadence | None = None
    branch_count_range: BranchCountRange | None = None
    length_preference: LengthPreference | None = None
    schema_version: Literal[1] = 1


class WritingSetupStateDTO(BaseModel):
    """Currently-persisted Writing setup/config fields. Writing already
    bypasses SetupForm on reload once persisted visible state exists
    (StoryView's ``structuredSetupPersisted``), so no frontend hydration
    consumes this today -- included for GET .../setup symmetry across modes.
    Unlike ``WritingSetupRequest``, ``persona_id``/``specific_goals`` are
    optional here since setup may not have completed yet.
    """

    model_config = {"extra": "forbid"}

    mode: Literal["writing"]
    persona_id: str | None = None
    critique_intensity: CritiqueIntensity | None = None
    form: WritingForm | None = None
    form_other: str | None = None
    tense: str | None = None
    pov: str | None = None
    style_density: StyleDensity | None = None
    dialogue_narration_ratio: int | None = None
    genre_conventions: str | None = None
    specific_goals: str | None = None
    acceptable_content: str | None = None
    beat_constraints: list[str] | None = None
    schema_version: Literal[1] = 1


class SetupStateResponse(BaseModel):
    """Response for ``GET /api/stories/{story_id}/setup`` (PR #126 review
    round 5, P2): lets a setup form hydrate its initial state from what is
    already persisted, instead of always starting from hardcoded defaults
    and silently overwriting a prior save on the next submit.
    """

    model_config = {"extra": "forbid"}

    setup_state: (
        RpgSetupStateDTO | BranchingSetupStateDTO | WritingSetupStateDTO | None
    ) = None
    schema_version: Literal[1] = 1


class VisibleStateResponse(BaseModel):
    model_config = {"extra": "forbid"}

    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1


class PersonaDTO(BaseModel):
    model_config = {"extra": "forbid"}

    persona_id: str
    display_name: str
    orientation: str
    ui_short_description: str
    ui_long_description: str
    demeanor_tags: list[str]
    signature_move: str
    schema_version: Literal[1] = 1


class PersonaGalleryResponse(BaseModel):
    model_config = {"extra": "forbid"}

    mentors: list[PersonaDTO]
    peers: list[PersonaDTO]
    schema_version: Literal[1] = 1


class PendingInteractionResponse(BaseModel):
    """The story's RPG pending interaction (CRD Issue 15b, 15b-31): ``None``
    with no unresolved action sequence, else its player view -- a pending
    roll (adjustment options ride on it), a pending decision, or
    ``ready_for_narration``, whose affordance is the resume route. Player
    views only (15b-17): no stored snapshot or backend reference."""

    model_config = {"extra": "forbid"}

    interaction: ActionResolutionAdvanceResult | None = None
    schema_version: Literal[1] = 1


class RollAdjustmentRequest(BaseModel):
    """Apply one parameterless adjustment option of the pending roll
    (15b-9, 15b-10). Exact integers only, as for roll submissions."""

    model_config = {"extra": "forbid"}

    pending_roll_request_id: UUID
    expected_instruction_revision: StrictInt
    option_id: str
    schema_version: Literal[1] = 1


class TranscriptTurnDTO(BaseModel):
    model_config = {"extra": "forbid"}

    turn_id: UUID
    user_input: str
    assistant_output: str
    timestamp: datetime
    intent_classification: IntentType
    schema_version: Literal[1] = 1


class TranscriptResponse(BaseModel):
    model_config = {"extra": "forbid"}

    turns: list[TranscriptTurnDTO]
    schema_version: Literal[1] = 1


# ---------------------------------------------------------------------------
# CRD Issue 20: account (billing/Cloud Services) and BYOK settings
# ---------------------------------------------------------------------------


class CloudServicesStatus(StrEnum):
    ACTIVE = "active"
    LAPSED = "lapsed"
    NOT_ACTIVATED = "not_activated"


class ByokProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"


class HostedCreditsDTO(BaseModel):
    """Authoritative hosted balances as exact decimal strings (four places).

    ``None`` = no hosted plan was ever activated; ``"0.0000"`` = depleted;
    negative values are shown as recorded, never clamped. Inactive hosted
    access keeps its balances (``hosted_unavailable_reason`` says why turns
    are unavailable).
    """

    model_config = {"extra": "forbid"}

    included: str | None
    top_up: str | None
    total: str | None
    hosted_turn_available: bool
    hosted_unavailable_reason: HostedUnavailableReason | None
    schema_version: Literal[1] = 1


class ByokProviderStateDTO(BaseModel):
    """Non-secret per-provider state; no key material or fragment of it.

    ``credential_present`` is None when the credential store could not be
    read (unknown, not absent). ``enabled``/``validation_status`` are None
    when no credential metadata exists for the provider.
    """

    model_config = {"extra": "forbid"}

    provider: ByokProvider
    credential_present: bool | None
    enabled: bool | None
    validation_status: ValidationStatus | None
    last_validated_at: datetime | None
    schema_version: Literal[1] = 1


class ByokReadinessSource(StrEnum):
    """Where ``byok_ready`` comes from (prerequisite #205 §3).

    ``local_device``: this installation's own credential store. A remote
    deployment never reads a device: ``unavailable_remotely`` means local
    readiness is unknown here, not absent, and ``byok_ready`` is then None.
    """

    LOCAL_DEVICE = "local_device"
    UNAVAILABLE_REMOTELY = "unavailable_remotely"


class ByokStatusDTO(BaseModel):
    """``byok_ready`` is the shared resolver/readiness predicate; None when
    that probe failed (a turn then treats BYOK as not runnable) or when
    ``readiness_source`` is ``unavailable_remotely``."""

    model_config = {"extra": "forbid"}

    license_active: bool
    credential_store_writable: bool
    providers: list[ByokProviderStateDTO]
    openrouter_model: str | None
    byok_ready: bool | None
    readiness_source: ByokReadinessSource = ByokReadinessSource.LOCAL_DEVICE
    schema_version: Literal[1] = 1


class AccountStatusResponse(BaseModel):
    """Authoritative account view (CRD Issue 20).

    ``selected_access_path`` is what the server would select for a turn
    started now (None = blocked with ``blocked_error_code``). The three
    ``*_available`` flags are fixed False: numeric usage estimates await
    calibration, and purchasing/trial enrollment belong to CRD Issue 23.
    """

    model_config = {"extra": "forbid"}

    credits: HostedCreditsDTO
    cloud_services: CloudServicesStatus
    byok: ByokStatusDTO
    selected_access_path: RuntimeAccessPath | None
    blocked_error_code: ApiErrorCode | None
    usage_estimate_available: Literal[False] = False
    purchase_available: Literal[False] = False
    trial_enrollment_available: Literal[False] = False
    refreshed_at: datetime
    schema_version: Literal[1] = 1


class CredentialWriteRequest(BaseModel):
    """Raw key, transient: handed to the credential store, never echoed."""

    model_config = {"extra": "forbid"}

    api_key: SecretStr = Field(min_length=1, max_length=512)
    schema_version: Literal[1] = 1


class ProviderEnabledRequest(BaseModel):
    model_config = {"extra": "forbid"}

    enabled: StrictBool
    schema_version: Literal[1] = 1


class OpenRouterModelRequest(BaseModel):
    """``None`` clears the model (OpenRouter is then not runnable)."""

    model_config = {"extra": "forbid"}

    model_identifier: str | None = Field(max_length=256)
    schema_version: Literal[1] = 1


class CredentialValidationRequest(BaseModel):
    """Validation contacts the provider and may incur provider usage; the
    client must acknowledge that explicitly."""

    model_config = {"extra": "forbid"}

    acknowledge_provider_contact: Literal[True]
    schema_version: Literal[1] = 1


# ---------------------------------------------------------------------------
# RPG product startup (ADR-015c)
# ---------------------------------------------------------------------------


class RpgRulesPackageOptionDTO(BaseModel):
    model_config = {"extra": "forbid"}

    package_uuid: UUID
    name: str
    system: str
    version: str
    schema_version: Literal[1] = 1


class RpgWorldTargetDTO(BaseModel):
    model_config = {"extra": "forbid"}

    turn_id: UUID
    world_revision: int
    understanding: str
    schema_version: Literal[1] = 1


class RpgSheetRowDTO(BaseModel):
    """One readable line of a candidate sheet (display only)."""

    model_config = {"extra": "forbid"}

    label: str
    value: str
    schema_version: Literal[1] = 1


class RpgCharacterCandidateDTO(BaseModel):
    """The reviewable, unaccepted candidate. ``problems`` empty means it can
    be accepted; chat prose is never the authoritative sheet."""

    model_config = {"extra": "forbid"}

    revision: int
    path: Literal["gm_led", "completed_sheet"]
    sheet: list[RpgSheetRowDTO]
    unresolved: list[str]
    problems: list[str]
    schema_version: Literal[1] = 1


class RpgSetupConfigurationDTO(BaseModel):
    model_config = {"extra": "forbid"}

    dice_handling: DiceHandling
    gm_cheating: bool
    tone: RpgTone
    session_type: RpgSessionType
    genre_flavor: str | None = None
    house_rules: str | None = None
    acceptable_content: str | None = None
    schema_version: Literal[1] = 1


class RpgSetupViewDTO(BaseModel):
    """Authoritative RPG pre-play progress, restored on every reload."""

    model_config = {"extra": "forbid"}

    phase: Literal[
        "world_setup", "character_creation", "play_configuration", "complete"
    ]
    play_status: Literal["setup", "in_play"]
    world_revision: int
    world_target: RpgWorldTargetDTO | None
    packages: list[RpgRulesPackageOptionDTO]
    selected_package_uuid: UUID | None
    candidate: RpgCharacterCandidateDTO | None
    character_accepted: bool
    configuration: RpgSetupConfigurationDTO
    configuration_revision: int = 0
    configuration_target: RpgConfigurationTargetDTO | None = None
    schema_version: Literal[1] = 1


class RpgConfirmWorldRequest(BaseModel):
    model_config = {"extra": "forbid"}

    expected_world_revision: StrictInt
    schema_version: Literal[1] = 1


class RpgSelectRulesPackageRequest(BaseModel):
    model_config = {"extra": "forbid"}

    package_uuid: UUID
    schema_version: Literal[1] = 1


class RpgAcceptCharacterRequest(BaseModel):
    model_config = {"extra": "forbid"}

    expected_candidate_revision: StrictInt
    schema_version: Literal[1] = 1


class RpgConfigurationTargetDTO(BaseModel):
    """What the GM's delivered summary presented for confirmation."""

    model_config = {"extra": "forbid"}

    turn_id: UUID
    configuration_revision: int
    configuration: RpgSetupConfigurationDTO
    summary: str
    schema_version: Literal[1] = 1


class RpgCompleteSetupRequest(BaseModel):
    """Confirm the configuration the GM summarized, at its revision."""

    model_config = {"extra": "forbid"}

    expected_configuration_revision: StrictInt
    schema_version: Literal[1] = 1


# ---------------------------------------------------------------------------
# Remote identity (prerequisite #205; ADR-021). Credentials are SecretStr:
# never echoed, logged or returned.
# ---------------------------------------------------------------------------


class DeploymentKind(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


class SessionStatusResponse(BaseModel):
    """Presentation state only -- never authority. ``signed_in`` is always
    False for a local deployment, which needs no sign-in."""

    model_config = {"extra": "forbid"}

    deployment: DeploymentKind
    signed_in: bool
    account_id: UUID | None = None
    contact_address: str | None = None
    schema_version: Literal[1] = 1


class AcceptedResponse(BaseModel):
    """Identical for every outcome, so it reveals no account's existence."""

    model_config = {"extra": "forbid"}

    status: Literal["accepted"] = "accepted"
    schema_version: Literal[1] = 1


class ContactAddressRequest(BaseModel):
    model_config = {"extra": "forbid"}

    contact_address: str = Field(min_length=3, max_length=320)
    schema_version: Literal[1] = 1


class CompleteEnrollmentRequest(BaseModel):
    model_config = {"extra": "forbid"}

    contact_address: str = Field(min_length=3, max_length=320)
    code: SecretStr = Field(min_length=1, max_length=128)
    password: SecretStr = Field(min_length=1, max_length=1024)
    schema_version: Literal[1] = 1


class SignInRequest(BaseModel):
    model_config = {"extra": "forbid"}

    contact_address: str = Field(min_length=1, max_length=320)
    password: SecretStr = Field(min_length=1, max_length=1024)
    schema_version: Literal[1] = 1


class CompleteRecoveryRequest(BaseModel):
    model_config = {"extra": "forbid"}

    contact_address: str = Field(min_length=3, max_length=320)
    code: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=1, max_length=1024)
    schema_version: Literal[1] = 1


class CloseAccountRequest(BaseModel):
    model_config = {"extra": "forbid"}

    password: SecretStr = Field(min_length=1, max_length=1024)
    schema_version: Literal[1] = 1


class StaffSessionResponse(BaseModel):
    model_config = {"extra": "forbid"}

    signed_in: bool
    expires_at: datetime | None = None
    schema_version: Literal[1] = 1


class ReplayCheckDTO(BaseModel):
    """Replay of the ordered ledger compared with the projection -- reported,
    never repaired."""

    model_config = {"extra": "forbid"}

    status: Literal["consistent", "mismatch", "unreadable", "absent"]
    detail_code: str | None = None
    through_sequence: int | None = None
    mismatched_fields: list[str] = Field(default_factory=list)
    schema_version: Literal[1] = 1


class AdminAccountViewResponse(BaseModel):
    """Owner-administrator view of one deliberately targeted hosted account.

    Allowlisted, non-secret operational metadata only: no contact address,
    Story content, credential or local-device state."""

    model_config = {"extra": "forbid"}

    account_id: UUID
    status: Literal["active", "closed"]
    created_at: datetime
    closed_at: datetime | None
    owned_story_count: int
    credits: HostedCreditsDTO
    cloud_services: CloudServicesStatus
    byok_license_active: bool
    byok_readiness_source: ByokReadinessSource
    # CRD Issue 22 support lookup: owning-source state, read-only.
    #: "absent": no entitlement projection exists (never "zero").
    entitlement_state: Literal["absent", "present"] = "absent"
    hosted_access_active: bool = False
    hosted_plan: str | None = None
    cloud_services_expires_at: datetime | None = None
    byok_license_purchased_at: datetime | None = None
    #: Stale-state token for a remediation preview.
    last_entitlement_event_id: UUID | None = None
    #: Expected conditions, not anomalies: negative_balance,
    #: credits_exhausted, hosted_inactive, cloud_services_lapsed.
    expected_conditions: list[str] = Field(default_factory=list)
    replay: ReplayCheckDTO | None = None
    schema_version: Literal[1] = 1


class RevokeSessionsRequest(BaseModel):
    model_config = {"extra": "forbid"}

    reason: str = Field(min_length=1, max_length=280)
    schema_version: Literal[1] = 1


class RevokeSessionsResponse(BaseModel):
    model_config = {"extra": "forbid"}

    account_id: UUID
    revoked_sessions: int
    schema_version: Literal[1] = 1


# ---------------------------------------------------------------------------
# CRD Issue 22 support, history and remediation (Owner administrator only).
# Untrusted text (reasons) is returned as plain text, never markup.
# ---------------------------------------------------------------------------


class EntitlementHistoryItemDTO(BaseModel):
    """One entitlement event's allowlisted effect fields. Free-text
    ``detail`` is never shown (``has_detail`` says one exists)."""

    model_config = {"extra": "forbid"}

    global_sequence: int
    event_id: UUID
    event_type: str
    created_at: datetime
    turn_id: UUID | None = None
    support_operation_id: UUID | None = None
    plan: str | None = None
    hosted_credit_delta: str | None = None
    top_up_credit_delta: str | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    purchased_at: datetime | None = None
    reason_code: str | None = None
    manual_reason: str | None = None
    adjusted_by: str | None = None
    external_source: str | None = None
    external_reference_id: str | None = None
    has_detail: bool = False
    parse_error: str | None = None
    schema_version: Literal[1] = 1


class EntitlementHistoryResponse(BaseModel):
    """A page of the subject's entitlement events in replay order
    (``global_sequence`` ascending, strictly after ``after_sequence``).
    ``next_after_sequence`` continues it; None means this page is the end."""

    model_config = {"extra": "forbid"}

    account_id: UUID
    order: Literal["global_sequence_ascending"] = "global_sequence_ascending"
    after_sequence: int
    events: list[EntitlementHistoryItemDTO]
    total_events: int
    next_after_sequence: int | None
    replay: ReplayCheckDTO
    schema_version: Literal[1] = 1


class SupportEventDTO(BaseModel):
    model_config = {"extra": "forbid"}

    event_id: UUID
    event_order: int
    operation_id: UUID
    actor_ref: str
    action_code: str
    target_type: str
    target_ref: str
    reason_code: str
    reason_text: str | None
    hosted_credit_delta: str | None
    top_up_credit_delta: str | None
    requested_at: datetime
    recorded_at: datetime
    outcome_code: str
    source_entitlement_event_id: UUID | None
    supersedes_event_id: UUID | None
    schema_version: Literal[1] = 1


class SupportHistoryResponse(BaseModel):
    """The account's support stream in its own ``event_order``. Correlate with
    entitlement history by ``source_entitlement_event_id`` only."""

    model_config = {"extra": "forbid"}

    account_id: UUID
    events: list[SupportEventDTO]
    schema_version: Literal[1] = 1


class CreditAdjustmentPreviewRequest(BaseModel):
    model_config = {"extra": "forbid"}

    hosted_credit_delta: str | None = Field(default=None, max_length=32)
    top_up_credit_delta: str | None = Field(default=None, max_length=32)
    schema_version: Literal[1] = 1


class CreditAdjustmentPreviewResponse(BaseModel):
    """Target, signed deltas, current and resulting balances, and the
    stale-state token to submit with the adjustment."""

    model_config = {"extra": "forbid"}

    account_id: UUID
    current: HostedCreditsDTO
    hosted_credit_delta: str
    top_up_credit_delta: str
    resulting_included: str | None
    resulting_top_up: str | None
    last_entitlement_event_id: UUID | None
    #: Why the entitlement owner would refuse it now (no effect would occur).
    refusal_code: str | None
    schema_version: Literal[1] = 1


class CreditAdjustmentRequest(BaseModel):
    """``operation_id`` is the logical action's stable identity: resubmit the
    same one after an uncertain result; never mint a new one to retry."""

    model_config = {"extra": "forbid"}

    operation_id: UUID
    hosted_credit_delta: str | None = Field(default=None, max_length=32)
    top_up_credit_delta: str | None = Field(default=None, max_length=32)
    reason: str = Field(min_length=1, max_length=280)
    expected_last_entitlement_event_id: UUID | None
    schema_version: Literal[1] = 1


class SupportOperationResponse(BaseModel):
    """Authoritative outcome: ``committed`` only with its entitlement event
    and refreshed balances; ``requested`` means not yet confirmed."""

    model_config = {"extra": "forbid"}

    operation_id: UUID
    outcome_code: str
    source_entitlement_event_id: UUID | None
    events: list[SupportEventDTO]
    account: AdminAccountViewResponse | None = None
    schema_version: Literal[1] = 1

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

from pydantic import BaseModel, Field, field_validator

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
from afterworlds.models.rpg import RpgVisibleState
from afterworlds.pipeline.branching.models import BranchingVisibleState
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
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


class PersonaGalleryResponse(BaseModel):
    model_config = {"extra": "forbid"}

    mentors: list[PersonaDTO]
    peers: list[PersonaDTO]
    schema_version: Literal[1] = 1


class TranscriptTurnDTO(BaseModel):
    model_config = {"extra": "forbid"}

    turn_id: UUID
    user_input: str
    assistant_output: str
    timestamp: datetime
    intent_classification: IntentType


class TranscriptResponse(BaseModel):
    model_config = {"extra": "forbid"}

    turns: list[TranscriptTurnDTO]
    schema_version: Literal[1] = 1
